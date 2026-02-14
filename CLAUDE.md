# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a UCI (Union Cycliste Internationale) rider data scraper that extracts professional road cyclist information from the UCI website, stores it in PostgreSQL with SCD2 change tracking, and uploads merged data to AWS S3.

## Local Development Setup

```bash
# One-time setup: create venv, install dependencies, and install Playwright browser
./setup-local.sh

# Activate virtual environment
source .venv/bin/activate

# Start PostgreSQL and LocalStack
docker-compose up -d

# Run the scraper
python -m riders
```

## Docker Testing with LocalStack

```bash
# Run scraper in Docker with LocalStack S3 and PostgreSQL
docker-compose --profile run up --build

# Or start PostgreSQL and LocalStack only (for local Python development)
docker-compose up -d

# Verify S3 bucket was created
aws --endpoint-url=http://localhost:4566 s3 ls
```

## Build and Run Commands

```bash
# Build Docker image
docker build -t riders-list .

# Run in Docker with real AWS
docker run --env-file .env riders-list
```

## Architecture

Multi-module application with 4 phases:

1. **Scrape** (`riders/scraper.py`) — Playwright async scraping of UCI rider pages
2. **Upsert** (`riders/db.py`) — SCD2 change tracking in PostgreSQL
3. **Export** (`riders/db.py`) — Merged view (scraped + overrides) to JSON
4. **Upload** (`riders/s3.py`) — JSON file to S3

Entry point: `riders/__main__.py` orchestrates all phases (`python -m riders`).

### Database Schema

- `riders_scraped` — SCD2 history table (tracks every change per rider)
- `riders_overrides` — Manual corrections and enrichment data
- `riders_current` — View merging scraped + overrides (export-ready); excludes riders with `scraped_at` older than 7 days (staleness filter for removed riders)

Migrations managed by yoyo-migrations in `migrations/`.

## Dependencies

- **playwright**: Async web scraping with Chromium
- **boto3**: AWS S3 uploads
- **python-dotenv**: Environment variable loading
- **psycopg[binary]**: PostgreSQL driver (v3)
- **yoyo-migrations**: SQL migration runner

## Environment Variables

Copy `.env.example` to `.env` and fill in the values.

Required:
- `DB_URL` — PostgreSQL connection string
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `S3_BUCKET_NAME`

Optional:
- `S3_ENDPOINT_URL` - Set to `http://localhost:4566` for LocalStack
- `SCRAPER_MAX_CONCURRENT` - Number of concurrent requests (default: 20)
- `SCRAPER_REQUEST_DELAY` - Delay between requests in seconds (default: 0.1)

## Conventions

- Use [Conventional Commits](https://www.conventionalcommits.org/) for all commit messages (e.g. `feat:`, `fix:`, `refactor:`, `docs:`, `chore:`).
