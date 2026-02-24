from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from velodex.web.routers import admin, auth, overrides, riders

app = FastAPI(
    title="Velodex",
    description=(
        "UCI professional road cyclist data platform. "
        "Scrapes rider profiles from the UCI website, tracks changes with SCD2 history in PostgreSQL, "
        "allows manual corrections via an admin UI, and exports merged data to AWS S3.\n\n"
        "**Authentication**: Protected endpoints require an `access_token` HTTP-only cookie "
        "set by `/api/auth/login` or `/api/auth/register`. "
        "Access tokens expire after 15 minutes; use `/api/auth/refresh` to renew via the "
        "refresh cookie (7-day TTL)."
    ),
    version="1.0.0",
)

app.include_router(auth.router)
app.include_router(riders.router)
app.include_router(overrides.router)
app.include_router(admin.router)

# ── SPA static files ─────────────────────────────────────────────────────

UI_DIST = Path(__file__).resolve().parent.parent.parent / "ui" / "dist"

if UI_DIST.is_dir():
    app.mount("/assets", StaticFiles(directory=UI_DIST / "assets"), name="assets")

    @app.get("/{full_path:path}")
    def spa_catch_all(full_path: str):
        file = UI_DIST / full_path
        if file.is_file():
            return FileResponse(file)
        return FileResponse(UI_DIST / "index.html")
