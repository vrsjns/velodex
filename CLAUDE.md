# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a UCI (Union Cycliste Internationale) rider data scraper that extracts professional road cyclist information from the UCI website and uploads it to AWS S3.

## Local Development Setup

```bash
# One-time setup: create venv and install dependencies
./setup-local.sh

# Activate virtual environment
source .venv/bin/activate

# Run the scraper (requires Chrome installed locally)
python create-riders-list.py
```

## Docker Testing with LocalStack

```bash
# Run scraper in Docker with LocalStack S3
docker-compose --profile run up --build

# Or start LocalStack only (for local Python development)
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

Single-script application (`create-riders-list.py`) that:
1. Uses Selenium with headless Chrome to scrape UCI rider pages (161 pages total)
2. Extracts rider name, nationality, birth date, and sanctions status
3. Saves data locally to `uci_riders.json`
4. Uploads the JSON file to an S3 bucket

## Dependencies

- **selenium** / **webdriver-manager**: Web scraping with Chrome
- **boto3**: AWS S3 uploads
- **python-dotenv**: Environment variable loading

## Environment Variables

Copy `.env.example` to `.env` and fill in the values.

Required:
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `S3_BUCKET_NAME`

Optional:
- `S3_ENDPOINT_URL` - Set to `http://localhost:4566` for LocalStack
