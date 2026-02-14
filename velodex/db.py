import hashlib
import logging
import os
from pathlib import Path
from datetime import datetime, timezone

import psycopg
from yoyo import read_migrations, get_backend

logger = logging.getLogger(__name__)

MIGRATIONS_DIR = str(Path(__file__).parent.parent / "migrations")


def get_db_url() -> str:
    url = os.getenv("DB_URL")
    if not url:
        raise RuntimeError("DB_URL environment variable is required")
    return url


def run_migrations():
    """Apply pending yoyo migrations."""
    db_url = get_db_url()
    logger.info("Running database migrations...")
    backend = get_backend(db_url)
    migrations = read_migrations(MIGRATIONS_DIR)
    with backend.lock():
        backend.apply_migrations(backend.to_apply(migrations))
    logger.info("Migrations complete")


def compute_row_hash(name: str, nationality: str, birth_date: str, sanctions: str) -> str:
    """MD5 hash of data fields — used to detect changes between scrape runs."""
    payload = "|".join([name or "", nationality or "", birth_date or "", sanctions or ""])
    return hashlib.md5(payload.encode()).hexdigest()


def load_current_hashes(conn) -> dict[tuple[str, str], str]:
    """Bulk-fetch {(source, source_url): row_hash} for all current rows."""
    with conn.cursor() as cur:
        cur.execute("SELECT source, source_url, row_hash FROM riders_scraped WHERE is_current")
        return {(row[0], row[1]): row[2] for row in cur.fetchall()}


def upsert_riders(conn, riders: list[dict], source: str = "uci"):
    """SCD2 upsert: new riders INSERT, unchanged bump scraped_at, changed close+insert.

    `riders` is a list of dicts with keys: source_url, name, nationality, birth_date, sanctions.
    All writes happen in a single transaction.
    """
    now = datetime.now(timezone.utc)
    current_hashes = load_current_hashes(conn)

    new_rows = []
    updated_rows = []  # (source, source_url, new rider dict, new hash)
    bumped_keys = []

    for rider in riders:
        url = rider["source_url"]
        key = (source, url)
        h = compute_row_hash(rider["name"], rider["nationality"], rider["birth_date"], rider["sanctions"])
        existing_hash = current_hashes.get(key)

        if existing_hash is None:
            new_rows.append((rider, h))
        elif existing_hash == h:
            bumped_keys.append(key)
        else:
            updated_rows.append((source, url, rider, h))

    with conn.cursor() as cur:
        # Batch INSERT new riders
        if new_rows:
            values = [
                (source, r["source_url"], r["name"], r["nationality"], r["birth_date"], r["sanctions"], now, now, h)
                for r, h in new_rows
            ]
            cur.executemany(
                """INSERT INTO riders_scraped
                   (source, source_url, name, nationality, birth_date, sanctions, valid_from, scraped_at, row_hash)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                values,
            )

        # Bump scraped_at for unchanged
        if bumped_keys:
            cur.executemany(
                "UPDATE riders_scraped SET scraped_at = %s WHERE source = %s AND source_url = %s AND is_current",
                [(now, s, u) for s, u in bumped_keys],
            )

        # Close old + insert new for changed
        if updated_rows:
            # Close old rows
            cur.executemany(
                """UPDATE riders_scraped
                   SET valid_to = %s, is_current = FALSE
                   WHERE source = %s AND source_url = %s AND is_current""",
                [(now, s, u) for s, u, _, _ in updated_rows],
            )
            # Insert new current rows
            cur.executemany(
                """INSERT INTO riders_scraped
                   (source, source_url, name, nationality, birth_date, sanctions, valid_from, scraped_at, row_hash)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                [
                    (s, u, r["name"], r["nationality"], r["birth_date"], r["sanctions"], now, now, h)
                    for s, u, r, h in updated_rows
                ],
            )

    # Count stale rows (current but not seen for 7+ days)
    with conn.cursor() as cur:
        cur.execute(
            "SELECT count(*) FROM riders_scraped WHERE is_current AND scraped_at <= now() - INTERVAL '7 days'"
        )
        stale_count = cur.fetchone()[0]

    conn.commit()
    logger.info(
        f"SCD2 upsert: {len(new_rows)} new, {len(bumped_keys)} unchanged, "
        f"{len(updated_rows)} changed, {stale_count} stale"
    )


def export_merged(conn) -> list[dict]:
    """SELECT from riders_current view and return as list of dicts."""
    with conn.cursor() as cur:
        cur.execute(
            """SELECT source, source_url, name, nationality, birth_date, sanctions,
                      team, instagram, notes, scraped_at, valid_from
               FROM riders_current
               ORDER BY name"""
        )
        columns = [desc[0] for desc in cur.description]
        rows = cur.fetchall()

    results = []
    for row in rows:
        d = dict(zip(columns, row))
        # Convert datetimes to ISO strings for JSON serialization
        for key in ("scraped_at", "valid_from"):
            if d[key] is not None:
                d[key] = d[key].isoformat()
        # Drop None-valued enrichment fields to keep JSON clean
        results.append({k: v for k, v in d.items() if v is not None})

    logger.info(f"Exported {len(results)} riders from merged view")
    return results


def connect():
    """Open a psycopg connection using DB_URL."""
    return psycopg.connect(get_db_url())
