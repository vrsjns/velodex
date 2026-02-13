import asyncio
import logging
import re

from playwright.async_api import async_playwright, Browser, BrowserContext

logger = logging.getLogger(__name__)

BASE_DOMAIN = "https://www.uci.org"
BASE_URL = "https://www.uci.org/riders/road-riders-teams/4uEfOErsvL4hkRJriqkdiw?tab=riders-list-riders&page={page}"
MAX_RETRIES = 3


async def create_browser():
    """Launch a single browser instance."""
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True)
    return browser, playwright


async def get_total_pages(browser: Browser) -> int:
    """Detect total pages from pagination."""
    logger.info("Detecting total number of pages...")
    context = await browser.new_context()
    page = await context.new_page()

    try:
        await page.goto(BASE_URL.format(page=1))
        await page.wait_for_selector('.riders-list__item-container', timeout=15000)
        logger.info("Rider list loaded, looking for pagination...")

        await page.wait_for_selector('.pager__item--last-page a', timeout=10000)
        href = await page.get_attribute('.pager__item--last-page a', 'href')
        max_page = int(href.split('page=')[-1].split('&')[0])

        logger.info(f"Detected {max_page} total pages")
        return max_page
    finally:
        await context.close()


async def collect_page_urls(
    context: BrowserContext,
    page_num: int,
    semaphore: asyncio.Semaphore
) -> dict:
    """Collect rider URLs from a single page."""
    async with semaphore:
        page = await context.new_page()
        try:
            await page.goto(BASE_URL.format(page=page_num))
            await page.wait_for_selector('.riders-list__item-container', timeout=10000)

            cards = await page.query_selector_all('.riders-list__item-container')
            urls = []
            for card in cards:
                url = await card.get_attribute('href')
                if url:
                    if url.startswith('/'):
                        url = BASE_DOMAIN + url
                    urls.append(url)

            return {"success": True, "page": page_num, "urls": urls}
        except Exception as e:
            return {"success": False, "page": page_num, "urls": [], "error": str(e)}
        finally:
            await page.close()


async def collect_all_urls(browser: Browser, total_pages: int, max_concurrent: int) -> list:
    """Collect all rider profile URLs concurrently."""
    logger.info(f"Collecting URLs from {total_pages} pages ({max_concurrent} concurrent)...")

    semaphore = asyncio.Semaphore(max_concurrent)
    context = await browser.new_context()

    tasks = [
        collect_page_urls(context, p, semaphore)
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

    logger.info(f"URL collection complete: {len(all_urls)} URLs collected")
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
                        "source": "uci",
                        "source_url": url,
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
    """Scrape all rider profiles concurrently."""
    logger.info(f"Scraping {len(urls)} profiles ({max_concurrent} concurrent)...")

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

    logger.info(f"Scraping complete: {len(results)} successful, {len(errors)} errors")

    if errors:
        logger.warning(f"Failed URLs ({len(errors)}):")
        for err in errors[:10]:
            logger.warning(f"  {err['url']}: {err['error']}")
        if len(errors) > 10:
            logger.warning(f"  ... and {len(errors) - 10} more")

    return results, errors


async def run_scraper(max_concurrent: int, request_delay: float) -> list[dict]:
    """Full scrape pipeline: launch browser, collect URLs, scrape profiles.

    Returns list of rider dicts with keys: source, source_url, name, nationality, birth_date, sanctions.
    """
    logger.info(f"Starting UCI rider scraper (concurrent: {max_concurrent}, delay: {request_delay}s)")

    browser, playwright = await create_browser()
    logger.info("Browser initialized successfully")

    try:
        total_pages = await get_total_pages(browser)
        all_urls = await collect_all_urls(browser, total_pages, max_concurrent)

        if not all_urls:
            logger.error("No URLs collected. Exiting.")
            return []

        riders_data, errors = await scrape_all_profiles(browser, all_urls, max_concurrent, request_delay)
        logger.info(f"Total riders: {len(riders_data)}, Errors: {len(errors)}")
        return riders_data
    finally:
        await browser.close()
        await playwright.stop()
