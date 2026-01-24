import json
import os
import re
import logging
import sys
import asyncio

import boto3
from dotenv import load_dotenv
from playwright.async_api import async_playwright, Browser, BrowserContext

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Load variables from .env file
load_dotenv()
logger.info("Environment variables loaded")

# Configuration from environment
MAX_CONCURRENT = int(os.getenv("SCRAPER_MAX_CONCURRENT", "20"))
REQUEST_DELAY = float(os.getenv("SCRAPER_REQUEST_DELAY", "0.1"))
MAX_RETRIES = 3


async def create_browser():
    """Launch a single browser instance."""
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True)
    return browser, playwright


async def get_total_pages(browser: Browser, base_url: str) -> int:
    """Detect total pages from pagination."""
    logger.info("Detecting total number of pages...")
    context = await browser.new_context()
    page = await context.new_page()

    try:
        await page.goto(base_url.format(page=1))
        await page.wait_for_selector('.riders-list__item-container', timeout=15000)
        logger.info("Rider list loaded, looking for pagination...")

        await page.wait_for_selector('.pager__item--last-page a', timeout=10000)

        href = await page.get_attribute('.pager__item--last-page a', 'href')
        max_page = int(href.split('page=')[-1].split('&')[0])

        logger.info(f"Detected {max_page} total pages")
        return max_page
    finally:
        await context.close()


BASE_DOMAIN = "https://www.uci.org"


async def collect_page_urls(
    context: BrowserContext,
    page_num: int,
    base_url: str,
    semaphore: asyncio.Semaphore
) -> dict:
    """Collect rider URLs from a single page."""
    async with semaphore:
        page = await context.new_page()
        try:
            await page.goto(base_url.format(page=page_num))
            await page.wait_for_selector('.riders-list__item-container', timeout=10000)

            cards = await page.query_selector_all('.riders-list__item-container')
            urls = []
            for card in cards:
                url = await card.get_attribute('href')
                if url:
                    # Convert relative URLs to absolute
                    if url.startswith('/'):
                        url = BASE_DOMAIN + url
                    urls.append(url)

            return {"success": True, "page": page_num, "urls": urls}
        except Exception as e:
            return {"success": False, "page": page_num, "urls": [], "error": str(e)}
        finally:
            await page.close()


async def collect_all_urls(
    browser: Browser,
    base_url: str,
    total_pages: int,
    max_concurrent: int
) -> list:
    """Phase 1: Collect all URLs concurrently."""
    logger.info(f"Phase 1: Collecting URLs from {total_pages} pages ({max_concurrent} concurrent)...")

    semaphore = asyncio.Semaphore(max_concurrent)
    context = await browser.new_context()

    tasks = [
        collect_page_urls(context, p, base_url, semaphore)
        for p in range(1, total_pages + 1)
    ]

    completed = 0
    all_urls = []
    errors = []

    for coro in asyncio.as_completed(tasks):
        result = await coro
        completed += 1
        if completed % 20 == 0 or completed == total_pages:
            logger.info(f"  Progress: {completed}/{total_pages} pages processed")

        if result["success"]:
            all_urls.extend(result["urls"])
        else:
            errors.append({"page": result["page"], "error": result.get("error", "Unknown")})

    await context.close()

    if errors:
        logger.warning(f"Failed to collect URLs from {len(errors)} pages")

    logger.info(f"Phase 1 complete: {len(all_urls)} URLs collected")
    return all_urls


async def scrape_profile(
    context: BrowserContext,
    url: str,
    semaphore: asyncio.Semaphore,
    delay: float
) -> dict:
    """Scrape a single rider profile with retry logic."""
    async with semaphore:
        page = await context.new_page()
        last_error = None

        try:
            for attempt in range(MAX_RETRIES):
                try:
                    await page.goto(url)
                    await page.wait_for_selector('.rider-details__name', timeout=10000)

                    name = await page.inner_text('.rider-details__name')
                    values = await page.query_selector_all('.rider-details__footer-item__value')

                    nationality = await values[0].inner_text() if len(values) > 0 else ""
                    dob = await values[1].inner_text() if len(values) > 1 else ""
                    sanctions = await values[2].inner_text() if len(values) > 2 else ""

                    rider_data = {
                        "name": re.sub(r"\s+", " ", name.strip()),
                        "birth_date": re.sub(r"\s+", " ", dob.strip()),
                        "nationality": re.sub(r"\s+", " ", nationality.strip()),
                        "sanctions": re.sub(r"\s+", " ", sanctions.strip()),
                    }

                    if delay > 0:
                        await asyncio.sleep(delay)

                    return {"success": True, "data": rider_data, "url": url}

                except Exception as e:
                    last_error = e
                    if attempt < MAX_RETRIES - 1:
                        wait_time = (2 ** attempt) * 0.5
                        await asyncio.sleep(wait_time)
                    continue

            return {"success": False, "error": str(last_error), "url": url}
        finally:
            await page.close()


async def scrape_all_profiles(
    browser: Browser,
    urls: list,
    max_concurrent: int,
    delay: float
) -> tuple:
    """Phase 2: Scrape all profiles concurrently."""
    logger.info(f"Phase 2: Scraping {len(urls)} profiles ({max_concurrent} concurrent)...")

    semaphore = asyncio.Semaphore(max_concurrent)
    context = await browser.new_context()

    tasks = [scrape_profile(context, url, semaphore, delay) for url in urls]

    results = []
    errors = []
    completed = 0
    total_urls = len(urls)

    for coro in asyncio.as_completed(tasks):
        result = await coro
        completed += 1
        if completed % 100 == 0 or completed == total_urls:
            logger.info(f"  Progress: {completed}/{total_urls} profiles scraped")

        if result["success"]:
            results.append(result["data"])
        else:
            errors.append(result)

    await context.close()

    logger.info(f"Phase 2 complete: {len(results)} successful, {len(errors)} errors")

    if errors:
        logger.warning(f"Failed URLs ({len(errors)}):")
        for err in errors[:10]:
            logger.warning(f"  {err['url']}: {err['error']}")
        if len(errors) > 10:
            logger.warning(f"  ... and {len(errors) - 10} more")

    return results, errors


async def async_main():
    """Async entry point."""
    logger.info(f"Starting UCI rider scraper (concurrent: {MAX_CONCURRENT}, delay: {REQUEST_DELAY}s)")

    base_url = 'https://www.uci.org/riders/road-riders-teams/4uEfOErsvL4hkRJriqkdiw?tab=riders-list-riders&page={page}'

    browser, playwright = await create_browser()
    logger.info("Browser initialized successfully")

    try:
        total_pages = await get_total_pages(browser, base_url)
        all_urls = await collect_all_urls(browser, base_url, total_pages, MAX_CONCURRENT)

        if not all_urls:
            logger.error("No URLs collected. Exiting.")
            return

        riders_data, errors = await scrape_all_profiles(browser, all_urls, MAX_CONCURRENT, REQUEST_DELAY)

        logger.info(f"Scraping complete. Total riders: {len(riders_data)}, Errors: {len(errors)}")

        # Save to JSON
        local_file_path = "uci_riders.json"
        logger.info(f"Saving data to {local_file_path}...")
        with open(local_file_path, 'w', encoding='utf-8') as f:
            json.dump(riders_data, f, indent=2)
        logger.info(f"Saved {len(riders_data)} riders to {local_file_path}")

        # Upload to S3
        try:
            bucket_name = os.getenv("S3_BUCKET_NAME")
            object_name = "uci_riders.json"
            endpoint_url = os.getenv("S3_ENDPOINT_URL")

            logger.info(f"Uploading to S3 bucket '{bucket_name}'...")
            if endpoint_url:
                logger.info(f"  Using custom endpoint: {endpoint_url}")

            s3_config = {
                'aws_access_key_id': os.getenv("AWS_ACCESS_KEY_ID"),
                'aws_secret_access_key': os.getenv("AWS_SECRET_ACCESS_KEY"),
                'region_name': os.getenv("AWS_REGION"),
            }
            if endpoint_url:
                s3_config['endpoint_url'] = endpoint_url
            s3 = boto3.client('s3', **s3_config)

            s3.upload_file(local_file_path, bucket_name, object_name)
            logger.info(f"Uploaded {object_name} to S3 bucket '{bucket_name}' successfully")
        except Exception as e:
            logger.error(f"Failed to upload to S3: {e}")

    finally:
        await browser.close()
        await playwright.stop()
        logger.info("Done")


def main():
    """Main entry point."""
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
