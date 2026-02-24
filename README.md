# Velodex

UCI professional road cyclist data platform. Scrapes rider profiles from the UCI website, tracks changes with SCD2 history in PostgreSQL, allows manual corrections via an admin UI, and exports merged data to AWS S3.

## Features

- **Scraper** — Concurrent async scraping of UCI rider profiles using Playwright
- **SCD2 history** — Full change tracking per rider; only current records exported
- **Overrides** — Correct scraped data or add manual entries not on the UCI site
- **Export + S3 upload** — Merged rider JSON pushed to S3 after each scrape run
- **Web UI** — Browse/search riders, manage overrides, administer users
- **Auth** — JWT-based login with bcrypt passwords and role-based access (user/admin)

## Architecture

```
velodex/
├── velodex/
│   ├── __main__.py     # Scraper pipeline entry point
│   ├── scraper.py      # Playwright-based UCI scraper
│   ├── db.py           # SCD2 upserts, export query
│   ├── s3.py           # S3 upload
│   └── web/
│       ├── __main__.py # Startup: migrations, admin seed, uvicorn
│       ├── app.py      # FastAPI REST API
│       ├── auth.py     # JWT auth & password hashing
│       └── deps.py     # Dependency injection
├── ui/                 # React SPA (Vite + Tailwind v4 + Radix UI)
├── migrations/         # yoyo-migrations SQL files
├── Dockerfile          # Scraper image
├── Dockerfile.web      # Multi-stage web app image
└── docker-compose.yml  # PostgreSQL + LocalStack S3
```

### Scraper pipeline

Runs in four phases:

1. **Scrape** — Paginate UCI, collect profile URLs, scrape rider details concurrently
2. **Upsert** — SCD2: hash-detect changes, close old rows, insert new; bump `scraped_at` if unchanged
3. **Export** — Query merged view (`riders_current`) to JSON
4. **Upload** — Push JSON to S3 as `uci_riders.json`

### Database

| Table / View | Purpose |
|---|---|
| `riders_scraped` | SCD2 history; every data change creates a new row |
| `riders_overrides` | Manual corrections and enrichment (team, instagram, notes) |
| `riders_current` | View merging scraped + overrides; excludes riders unseen for 7+ days |
| `users` | Application users with `user` / `admin` roles |

Staleness filter: riders not seen in the last 7 days are excluded from `riders_current` (and therefore from exports), but remain in the history table.

### Override types

- **Correction** — Linked to a scraped rider via `source_url`; override fields win field-by-field in the merged view
- **Manual entry** — Standalone rider not on the UCI site; identified by a `manual_key`

## Local Development

### Prerequisites

- Python 3.11+
- Docker + Docker Compose
- Node.js 20+

### Setup

```bash
# Install Python deps, create venv, install Playwright browser
./setup-local.sh

# Activate venv
source .venv/bin/activate

# Start PostgreSQL and LocalStack
docker compose up -d

# Copy and fill in env vars
cp .env.example .env
```

### Running

```bash
# Run the scraper pipeline
python -m velodex

# Start the web app (API + serves built UI) on http://localhost:8000
python -m velodex.web

# UI dev server with hot reload on http://localhost:5173
cd ui && npm install && npm run dev
```

## Docker

```bash
# Start services only (PostgreSQL + LocalStack)
docker compose up -d

# Run scraper in Docker
docker compose --profile run up --build

# Run web app in Docker (builds UI, serves on :8000)
docker compose --profile web up --build

# Verify LocalStack S3 bucket
aws --endpoint-url=http://localhost:4566 s3 ls
```

## Environment Variables

Copy `.env.example` to `.env`.

| Variable | Required | Description |
|---|---|---|
| `DB_URL` | Yes | PostgreSQL connection string |
| `AWS_ACCESS_KEY_ID` | Yes | AWS / LocalStack key |
| `AWS_SECRET_ACCESS_KEY` | Yes | AWS / LocalStack secret |
| `AWS_REGION` | Yes | AWS region |
| `S3_BUCKET_NAME` | Yes | Target S3 bucket |
| `JWT_SECRET` | Yes | Secret for signing JWT tokens |
| `ADMIN_EMAIL` | Yes | Email for auto-seeded admin user |
| `ADMIN_PASSWORD` | Yes | Password for auto-seeded admin user |
| `S3_ENDPOINT_URL` | No | Set to `http://localhost:4566` for LocalStack |
| `SCRAPER_MAX_CONCURRENT` | No | Concurrent requests (default: 20) |
| `SCRAPER_REQUEST_DELAY` | No | Delay between requests in seconds (default: 0.1) |

## API

All endpoints require authentication (JWT in HTTP-only cookie) except login and register.

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/api/auth/register` | — | Register new user |
| `POST` | `/api/auth/login` | — | Login; sets access + refresh cookies |
| `POST` | `/api/auth/logout` | User | Clear cookies |
| `GET` | `/api/auth/me` | User | Current user info |
| `POST` | `/api/auth/refresh` | — | Refresh access token via refresh cookie |
| `PUT` | `/api/auth/profile` | User | Update own email / password |
| `GET` | `/api/riders` | User | List/search riders (`?q=<name>`) |
| `GET` | `/api/overrides` | Admin | List all overrides |
| `GET` | `/api/overrides/{id}` | Admin | Get single override |
| `POST` | `/api/overrides` | Admin | Create override or manual entry |
| `PUT` | `/api/overrides/{id}` | Admin | Update override |
| `DELETE` | `/api/overrides/{id}` | Admin | Delete override |
| `GET` | `/api/admin/users` | Admin | List all users |
| `PUT` | `/api/admin/users/{id}` | Admin | Update user (role, email, password) |
| `DELETE` | `/api/admin/users/{id}` | Admin | Delete user |

Access tokens expire after 15 minutes; refresh tokens after 7 days.

## Tech Stack

**Backend**
- Python 3.11+, FastAPI, uvicorn
- psycopg v3 (PostgreSQL), yoyo-migrations
- Playwright (async scraping), boto3 (S3)
- PyJWT, bcrypt

**Frontend**
- React 19, Vite 6, TypeScript
- Tailwind CSS v4, Radix UI primitives
- Style Dictionary (design tokens pipeline)
