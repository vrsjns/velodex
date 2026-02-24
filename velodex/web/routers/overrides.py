from typing import List, Optional

from fastapi import Depends, HTTPException, Security
from fastapi.routing import APIRouter
from pydantic import BaseModel

from velodex.web.auth import get_current_user, require_admin
from velodex.web.deps import cookie_scheme, get_db

router = APIRouter(prefix="/api", tags=["overrides"])


class OverrideOut(BaseModel):
    id: int
    source: Optional[str] = None
    source_url: Optional[str] = None
    name: Optional[str] = None
    nationality: Optional[str] = None
    birth_date: Optional[str] = None
    sanctions: Optional[str] = None
    team: Optional[str] = None
    instagram: Optional[str] = None
    notes: Optional[str] = None
    is_manual_entry: bool
    manual_key: Optional[str] = None
    reason: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class OverrideBody(BaseModel):
    source: Optional[str] = None
    source_url: Optional[str] = None
    name: Optional[str] = None
    nationality: Optional[str] = None
    birth_date: Optional[str] = None
    sanctions: Optional[str] = None
    team: Optional[str] = None
    instagram: Optional[str] = None
    notes: Optional[str] = None
    is_manual_entry: bool = False
    manual_key: Optional[str] = None
    reason: Optional[str] = None


def _empty_to_none(v):
    return v if v else None


def _fetch_override(override_id: int, conn):
    with conn.cursor() as cur:
        cur.execute(
            """SELECT id, source, source_url, name, nationality, birth_date,
                      sanctions, team, instagram, notes, is_manual_entry,
                      manual_key, reason, created_at, updated_at
               FROM riders_overrides WHERE id = %s""",
            (override_id,),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Override not found")
        columns = [desc[0] for desc in cur.description]
        d = dict(zip(columns, row))
        for key in ("created_at", "updated_at"):
            if d[key] is not None:
                d[key] = d[key].isoformat()
    return d


@router.get(
    "/overrides",
    summary="List all overrides",
    response_model=List[OverrideOut],
    dependencies=[Security(cookie_scheme), Depends(get_current_user)],
)
def api_overrides(conn=Depends(get_db)):
    with conn.cursor() as cur:
        cur.execute(
            """SELECT id, source, source_url, name, nationality, birth_date,
                      sanctions, team, instagram, notes, is_manual_entry,
                      manual_key, reason, created_at, updated_at
               FROM riders_overrides
               ORDER BY updated_at DESC"""
        )
        columns = [desc[0] for desc in cur.description]
        rows = []
        for row in cur.fetchall():
            d = dict(zip(columns, row))
            for key in ("created_at", "updated_at"):
                if d[key] is not None:
                    d[key] = d[key].isoformat()
            rows.append(d)
    return rows


@router.get(
    "/overrides/{override_id}",
    summary="Get override by ID",
    response_model=OverrideOut,
    dependencies=[Security(cookie_scheme), Depends(get_current_user)],
)
def api_override_detail(override_id: int, conn=Depends(get_db)):
    return _fetch_override(override_id, conn)


@router.post(
    "/overrides",
    summary="Create override or manual entry",
    description=(
        "Creates a data override or a standalone manual entry.\n\n"
        "**Correction** (`is_manual_entry=false`): link to a scraped rider via `source_url`; "
        "any non-null override fields win field-by-field in the merged view.\n\n"
        "**Manual entry** (`is_manual_entry=true`): a rider not on the UCI site, "
        "identified by a unique `manual_key`."
    ),
    response_model=OverrideOut,
    status_code=201,
    dependencies=[Security(cookie_scheme), Depends(require_admin)],
)
def api_override_create(body: OverrideBody, conn=Depends(get_db)):
    with conn.cursor() as cur:
        cur.execute(
            """INSERT INTO riders_overrides
               (source, source_url, name, nationality, birth_date, sanctions,
                team, instagram, notes, is_manual_entry, manual_key, reason)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
               RETURNING id""",
            (
                _empty_to_none(body.source),
                _empty_to_none(body.source_url),
                _empty_to_none(body.name),
                _empty_to_none(body.nationality),
                _empty_to_none(body.birth_date),
                _empty_to_none(body.sanctions),
                _empty_to_none(body.team),
                _empty_to_none(body.instagram),
                _empty_to_none(body.notes),
                body.is_manual_entry,
                _empty_to_none(body.manual_key),
                _empty_to_none(body.reason),
            ),
        )
        new_id = cur.fetchone()[0]
    conn.commit()
    return _fetch_override(new_id, conn)


@router.put(
    "/overrides/{override_id}",
    summary="Update override",
    response_model=OverrideOut,
    dependencies=[Security(cookie_scheme), Depends(require_admin)],
)
def api_override_update(override_id: int, body: OverrideBody, conn=Depends(get_db)):
    with conn.cursor() as cur:
        cur.execute(
            """UPDATE riders_overrides SET
                source = %s, source_url = %s, name = %s, nationality = %s,
                birth_date = %s, sanctions = %s, team = %s, instagram = %s,
                notes = %s, is_manual_entry = %s, manual_key = %s, reason = %s,
                updated_at = now()
               WHERE id = %s
               RETURNING id""",
            (
                _empty_to_none(body.source),
                _empty_to_none(body.source_url),
                _empty_to_none(body.name),
                _empty_to_none(body.nationality),
                _empty_to_none(body.birth_date),
                _empty_to_none(body.sanctions),
                _empty_to_none(body.team),
                _empty_to_none(body.instagram),
                _empty_to_none(body.notes),
                body.is_manual_entry,
                _empty_to_none(body.manual_key),
                _empty_to_none(body.reason),
                override_id,
            ),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Override not found")
    conn.commit()
    return _fetch_override(override_id, conn)


@router.delete(
    "/overrides/{override_id}",
    summary="Delete override",
    status_code=204,
    dependencies=[Security(cookie_scheme), Depends(require_admin)],
)
def api_override_delete(override_id: int, conn=Depends(get_db)):
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM riders_overrides WHERE id = %s RETURNING id",
            (override_id,),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Override not found")
    conn.commit()
