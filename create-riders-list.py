import json, os, time, re, logging, sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import boto3
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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
MAX_WORKERS = int(os.getenv("SCRAPER_MAX_WORKERS", "8"))
REQUEST_DELAY = float(os.getenv("SCRAPER_REQUEST_DELAY", "0.3"))
MAX_RETRIES = 3

# Thread-local storage for WebDriver instances
thread_local = threading.local()

# Lock for thread-safe logging of progress
progress_lock = threading.Lock()
completed_count = 0


def create_chrome_driver():
    """Create and configure a Chrome WebDriver instance."""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    return driver


def get_worker_driver():
    """Get or create a thread-local WebDriver instance."""
    if not hasattr(thread_local, 'driver'):
        thread_local.driver = create_chrome_driver()
    return thread_local.driver


def cleanup_worker_driver():
    """Clean up the thread-local WebDriver if it exists."""
    if hasattr(thread_local, 'driver'):
        try:
            thread_local.driver.quit()
        except Exception:
            pass
        delattr(thread_local, 'driver')


def get_total_pages(driver, base_url):
    """
    Detect total number of pages from UCI pagination.
    Navigates to the first page and extracts the last page number from the pager.
    """
    logger.info("Detecting total number of pages...")
    first_page_url = base_url.format(page=1)
    driver.get(first_page_url)

    # Wait for rider list to load (indicates page is ready)
    WebDriverWait(driver, 15).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.riders-list__item-container'))
    )
    logger.info("Rider list loaded, looking for pagination...")

    # Wait for pager and find the last page link
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '.pager__item--last-page a'))
    )

    last_page_link = driver.find_element(By.CSS_SELECTOR, '.pager__item--last-page a')
    href = last_page_link.get_attribute('href')
    # Extract page number from href like "/riders/...?page=132"
    max_page = int(href.split('page=')[-1].split('&')[0])

    logger.info(f"Detected {max_page} total pages")
    return max_page


def collect_page_urls(page, base_url, delay=REQUEST_DELAY):
    """
    Collect rider URLs from a single page.
    Uses thread-local driver for parallel execution.
    """
    driver = get_worker_driver()
    url = base_url.format(page=page)

    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.riders-list__item-container'))
        )

        rider_cards = driver.find_elements(By.CSS_SELECTOR, '.riders-list__item-container')
        page_urls = [card.get_attribute("href") for card in rider_cards if card.get_attribute("href")]

        if delay > 0:
            time.sleep(delay)

        return {"success": True, "page": page, "urls": page_urls}
    except Exception as e:
        return {"success": False, "page": page, "urls": [], "error": str(e)}


def parallel_collect_urls(base_url, total_pages, max_workers=MAX_WORKERS, delay=REQUEST_DELAY):
    """
    Phase 1: Collect rider URLs from all pages in parallel.
    Each worker maintains its own Chrome instance via thread-local storage.
    """
    logger.info(f"Phase 1: Collecting rider URLs from {total_pages} pages with {max_workers} workers...")

    all_urls = []
    errors = []
    pages_completed = 0

    def worker_task(page):
        nonlocal pages_completed
        result = collect_page_urls(page, base_url, delay)

        with progress_lock:
            pages_completed += 1
            if pages_completed % 20 == 0 or pages_completed == total_pages:
                logger.info(f"  Progress: {pages_completed}/{total_pages} pages processed")

        return result

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(worker_task, page): page for page in range(1, total_pages + 1)}

        for future in as_completed(futures):
            page = futures[future]
            try:
                result = future.result()
                if result["success"]:
                    all_urls.extend(result["urls"])
                else:
                    errors.append({"page": result["page"], "error": result.get("error", "Unknown")})
            except Exception as e:
                errors.append({"page": page, "error": str(e)})

    if errors:
        logger.warning(f"Failed to collect URLs from {len(errors)} pages")

    logger.info(f"Phase 1 complete: collected {len(all_urls)} rider URLs")
    return all_urls


def scrape_rider_profile(url, delay=REQUEST_DELAY):
    """
    Scrape a single rider profile page.
    Uses thread-local driver and implements retry logic.
    """
    global completed_count

    driver = get_worker_driver()
    last_error = None

    for attempt in range(MAX_RETRIES):
        try:
            driver.get(url)

            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.rider-details__name'))
            )

            name_element = driver.find_element(By.CSS_SELECTOR, '.rider-details__name')
            parent_element = driver.find_element(By.CSS_SELECTOR, '.rider-details__footer')
            nationality_element = parent_element.find_element(By.XPATH, "(//div[@class='rider-details__footer-item__value'])[1][1]")
            dob_element = parent_element.find_element(By.XPATH, "(//div[@class='rider-details__footer-item__value'])[2][1]")
            sanctions_element = parent_element.find_element(By.XPATH, "(//div[@class='rider-details__footer-item__value'])[3][1]")

            name = re.sub(r"\s+", " ", name_element.text.strip())
            nationality = re.sub(r"\s+", " ", nationality_element.text.strip())
            dob = re.sub(r"\s+", " ", dob_element.text.strip())
            sanctions = re.sub(r"\s+", " ", sanctions_element.text.strip())

            rider_data = {
                "name": name,
                "birth_date": dob,
                "nationality": nationality,
                "sanctions": sanctions
            }

            # Politeness delay
            if delay > 0:
                time.sleep(delay)

            return {"success": True, "data": rider_data, "url": url}

        except Exception as e:
            last_error = e
            if attempt < MAX_RETRIES - 1:
                # Exponential backoff
                wait_time = (2 ** attempt) * 0.5
                time.sleep(wait_time)
            continue

    return {"success": False, "error": str(last_error), "url": url}


def parallel_scrape_profiles(urls, max_workers=MAX_WORKERS, delay=REQUEST_DELAY):
    """
    Phase 2: Scrape rider profiles in parallel using ThreadPoolExecutor.
    Each worker maintains its own Chrome instance via thread-local storage.
    """
    global completed_count
    completed_count = 0

    total_urls = len(urls)
    logger.info(f"Phase 2: Starting parallel scrape with {max_workers} workers for {total_urls} profiles...")

    results = []
    errors = []

    def worker_task(url):
        global completed_count
        result = scrape_rider_profile(url, delay)

        with progress_lock:
            completed_count += 1
            if completed_count % 100 == 0 or completed_count == total_urls:
                logger.info(f"  Progress: {completed_count}/{total_urls} profiles scraped")

        return result

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(worker_task, url): url for url in urls}

        for future in as_completed(futures):
            url = futures[future]
            try:
                result = future.result()
                if result["success"]:
                    results.append(result["data"])
                else:
                    errors.append({"url": result["url"], "error": result["error"]})
            except Exception as e:
                errors.append({"url": url, "error": str(e)})

    logger.info(f"Phase 2 complete: {len(results)} successful, {len(errors)} errors")

    if errors:
        logger.warning(f"Failed URLs ({len(errors)}):")
        for err in errors[:10]:  # Show first 10 errors
            logger.warning(f"  {err['url']}: {err['error']}")
        if len(errors) > 10:
            logger.warning(f"  ... and {len(errors) - 10} more")

    return results, errors


def main():
    """Main entry point for the scraper."""
    logger.info(f"Starting UCI rider scraper (workers: {MAX_WORKERS}, delay: {REQUEST_DELAY}s)")

    # Main UCI riders page
    main_url = 'https://www.uci.org/riders/road-riders-teams/4uEfOErsvL4hkRJriqkdiw?tab=riders-list-riders&page={page}'

    # Create driver to detect total pages
    logger.info("Configuring Chrome options...")
    logger.info("Installing/locating ChromeDriver...")
    main_driver = create_chrome_driver()
    logger.info("ChromeDriver initialized successfully")

    try:
        # Get total pages
        total_pages = get_total_pages(main_driver, main_url)

        # Close driver before parallel phases
        main_driver.quit()
        main_driver = None

        # Phase 1: Parallel URL collection
        all_urls = parallel_collect_urls(main_url, total_pages, MAX_WORKERS, REQUEST_DELAY)

        if not all_urls:
            logger.error("No rider URLs collected. Exiting.")
            return

        # Phase 2: Parallel profile scraping
        riders_data, errors = parallel_scrape_profiles(all_urls, MAX_WORKERS, REQUEST_DELAY)

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
        # Clean up main driver if still open
        if main_driver:
            main_driver.quit()
        logger.info("Done")


if __name__ == "__main__":
    main()
