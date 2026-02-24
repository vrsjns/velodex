# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Velodex is a UCI (Union Cycliste Internationale) rider data platform. It scrapes professional road cyclist information from the UCI website, stores it in PostgreSQL with SCD2 change tracking, uploads merged data to AWS S3, and provides a web UI for browsing and managing rider data.

## Local Development Setup

```bash
# One-time setup: create venv, install dependencies, and install Playwright browser
./setup-local.sh

# Activate virtual environment
source .venv/bin/activate

# Start PostgreSQL and LocalStack
docker compose up -d

# Run the scraper
python -m velodex

# Run the web app (API + serves built UI)
python -m velodex.web

# UI development (separate terminal)
cd ui && npm install && npm run dev
```

## Docker

```bash
# Start PostgreSQL and LocalStack only (for local Python development)
docker compose up -d

# Run scraper in Docker with LocalStack S3 and PostgreSQL
docker compose --profile run up --build

# Run web app in Docker (builds UI, serves on port 8000)
docker compose --profile web up --build

# Build scraper Docker image
docker build -t velodex .

# Build web Docker image
docker build -f Dockerfile.web -t velodex-web .

# Verify S3 bucket was created
aws --endpoint-url=http://localhost:4566 s3 ls
```

## Architecture

### Scraper (`python -m velodex`)

Multi-phase pipeline orchestrated by `velodex/__main__.py`:

1. **Scrape** (`velodex/scraper.py`) — Playwright async scraping of UCI rider pages
2. **Upsert** (`velodex/db.py`) — SCD2 change tracking in PostgreSQL
3. **Export** (`velodex/db.py`) — Merged view (scraped + overrides) to JSON
4. **Upload** (`velodex/s3.py`) — JSON file to S3

### Web App (`python -m velodex.web`)

FastAPI backend + React SPA:

- **API** (`velodex/web/app.py`) — REST endpoints for riders, overrides, and admin user management
- **Auth** (`velodex/web/auth.py`) — JWT-based authentication with bcrypt passwords and cookie-based tokens
- **Deps** (`velodex/web/deps.py`) — FastAPI dependency injection (DB connection)
- **Startup** (`velodex/web/__main__.py`) — Runs migrations, seeds admin user, starts uvicorn

### React UI (`ui/`)

Vite + React SPA served by FastAPI in production. Pages:

- **RidersPage** — Browse/search riders
- **OverridesPage / OverrideForm** — Manage manual rider corrections (admin)
- **UsersPage** — Admin user management (roles, email, password reset)
- **ProfilePage** — Self-service email/password change
- **LoginPage / RegisterPage** — Authentication

### Database Schema

- `riders_scraped` — SCD2 history table (tracks every change per rider)
- `riders_overrides` — Manual corrections and enrichment data
- `riders_current` — View merging scraped + overrides (export-ready); excludes riders with `scraped_at` older than 7 days (staleness filter)
- `users` — Application users with roles (`user`, `admin`)

Migrations managed by yoyo-migrations in `migrations/`.

## Dependencies

Python:
- **playwright** — Async web scraping with Chromium
- **boto3** — AWS S3 uploads
- **python-dotenv** — Environment variable loading
- **psycopg[binary]** — PostgreSQL driver (v3)
- **yoyo-migrations** — SQL migration runner
- **fastapi** + **uvicorn** — Web API server
- **bcrypt** — Password hashing
- **PyJWT** — JSON Web Token auth

UI (`ui/package.json`):
- **react** + **react-dom** — Frontend framework
- **react-router-dom** — Client-side routing
- **vite** — Build tool

## Environment Variables

Copy `.env.example` to `.env` and fill in the values.

Required:
- `DB_URL` — PostgreSQL connection string
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `S3_BUCKET_NAME`

Auth (required for web app):
- `JWT_SECRET` — Secret key for signing JWT tokens
- `ADMIN_EMAIL` — Email for auto-seeded admin user
- `ADMIN_PASSWORD` — Password for auto-seeded admin user

Optional:
- `S3_ENDPOINT_URL` — Set to `http://localhost:4566` for LocalStack
- `SCRAPER_MAX_CONCURRENT` — Number of concurrent requests (default: 20)
- `SCRAPER_REQUEST_DELAY` — Delay between requests in seconds (default: 0.1)

## Conventions

- Use [Conventional Commits](https://www.conventionalcommits.org/) for all commit messages (e.g. `feat:`, `fix:`, `refactor:`, `docs:`, `chore:`).
