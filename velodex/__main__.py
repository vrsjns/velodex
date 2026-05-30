import json
import os
import logging
import sys
import asyncio

from dotenv import load_dotenv

from velodex.scraper import run_scraper
from velodex.db import run_migrations, connect, upsert_riders, export_merged
from velodex.s3 import upload_to_s3

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


async def async_main():
    """Orchestrate the 4 phases: scrape, upsert, export, upload."""

    # Phase 0: Run database migrations
    run_migrations()

    # Phase 1: Scrape UCI website
    logger.info("=== Phase 1: Scrape ===")
    riders_data = await run_scraper(MAX_CONCURRENT, REQUEST_DELAY)
    if not riders_data:
        logger.error("No riders scraped. Exiting.")
        return

    # Phase 2: Upsert to database (SCD2)
    logger.info("=== Phase 2: Upsert to DB ===")
    conn = connect()
    try:
        upsert_riders(conn, riders_data)

        # Phase 3: Export merged view to JSON
        logger.info("=== Phase 3: Export ===")
        merged = export_merged(conn)
    finally:
        conn.close()

    local_file_path = os.getenv("RIDERS_FILE", "riders.json")
    logger.info(f"Saving {len(merged)} riders to {local_file_path}...")
    with open(local_file_path, 'w', encoding='utf-8') as f:
        json.dump(merged, f, indent=2)

    # Phase 4: Upload to S3
    logger.info("=== Phase 4: Upload to S3 ===")
    try:
        upload_to_s3(local_file_path)
    except Exception as e:
        logger.error(f"Failed to upload to S3: {e}")

    logger.info("Done")


def main():
    """Main entry point."""
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
