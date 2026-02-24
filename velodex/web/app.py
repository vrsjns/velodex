from pathlib import Path
from typing import List, Optional

from fastapi import Cookie, Depends, FastAPI, HTTPException, Response, Security
from fastapi.responses import FileResponse
from fastapi.security import APIKeyCookie
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from velodex.web.deps import get_db
from velodex.web.auth import (
    clear_auth_cookies,
    create_user,
    decode_token,
    get_current_user,
    get_user_by_email,
    get_user_by_id,
    get_user_with_password,
    require_admin,
    set_auth_cookies,
    update_user_email,
    update_user_password,
    verify_password,
)

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

UI_DIST = Path(__file__).resolve().parent.parent.parent / "ui" / "dist"

cookie_scheme = APIKeyCookie(name="access_token", auto_error=False)


# ── Response models ───────────────────────────────────────────────────────


class UserOut(BaseModel):
    id: int
    email: str
    role: str


class RiderOut(BaseModel):
    source: Optional[str] = None
    source_url: Optional[str] = None
    name: Optional[str] = None
    nationality: Optional[str] = None
    birth_date: Optional[str] = None
    sanctions: Optional[str] = None
    team: Optional[str] = None
    instagram: Optional[str] = None
    notes: Optional[str] = None
    scraped_at: Optional[str] = None
    valid_from: Optional[str] = None


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


class AdminUserOut(BaseModel):
    id: int
    email: str
    role: str
    created_at: Optional[str] = None


# ── Auth endpoints ───────────────────────────────────────────────────────


class AuthBody(BaseModel):
    email: str
    password: str


@app.post(
    "/api/auth/register",
    tags=["auth"],
    summary="Register a new user",
    response_model=UserOut,
    status_code=201,
)
def auth_register(body: AuthBody, response: Response, conn=Depends(get_db)):
    existing = get_user_by_email(conn, body.email)
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")
    user = create_user(conn, body.email, body.password, role="user")
    set_auth_cookies(response, user["id"], user["role"])
    return {"id": user["id"], "email": user["email"], "role": user["role"]}


@app.post(
    "/api/auth/login",
    tags=["auth"],
    summary="Log in",
    response_model=UserOut,
)
def auth_login(body: AuthBody, response: Response, conn=Depends(get_db)):
    user = get_user_by_email(conn, body.email)
    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    set_auth_cookies(response, user["id"], user["role"])
    return {"id": user["id"], "email": user["email"], "role": user["role"]}


@app.post(
    "/api/auth/logout",
    tags=["auth"],
    summary="Log out",
)
def auth_logout(response: Response):
    clear_auth_cookies(response)
    return {"ok": True}


@app.get(
    "/api/auth/me",
    tags=["auth"],
    summary="Get current user",
    response_model=UserOut,
    dependencies=[Security(cookie_scheme)],
)
def auth_me(user=Depends(get_current_user)):
    return {"id": user["id"], "email": user["email"], "role": user["role"]}


@app.post(
    "/api/auth/refresh",
    tags=["auth"],
    summary="Refresh access token",
)
def auth_refresh(
    response: Response,
    refresh_token: str = Cookie(None),
    conn=Depends(get_db),
):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token")
    payload = decode_token(refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")
    user = get_user_by_id(conn, int(payload["sub"]))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    set_auth_cookies(response, user["id"], user["role"])
    return {"ok": True}


class ProfileBody(BaseModel):
    email: Optional[str] = None
    current_password: Optional[str] = None
    new_password: Optional[str] = None


@app.put(
    "/api/auth/profile",
    tags=["auth"],
    summary="Update own email or password",
    response_model=UserOut,
    dependencies=[Security(cookie_scheme)],
)
def auth_update_profile(
    body: ProfileBody,
    response: Response,
    user=Depends(get_current_user),
    conn=Depends(get_db),
):
    if body.email and body.email != user["email"]:
        existing = get_user_by_email(conn, body.email)
        if existing:
            raise HTTPException(status_code=409, detail="Email already taken")
        update_user_email(conn, user["id"], body.email)

    if body.new_password:
        if not body.current_password:
            raise HTTPException(status_code=400, detail="Current password is required")
        full_user = get_user_with_password(conn, user["id"])
        if not verify_password(body.current_password, full_user["password_hash"]):
            raise HTTPException(status_code=401, detail="Current password is incorrect")
        update_user_password(conn, user["id"], body.new_password)

    updated = get_user_by_id(conn, user["id"])
    set_auth_cookies(response, updated["id"], updated["role"])
    return {"id": updated["id"], "email": updated["email"], "role": updated["role"]}


# ── JSON API ─────────────────────────────────────────────────────────────


@app.get(
    "/api/riders",
    tags=["riders"],
    summary="List or search riders",
    response_model=List[RiderOut],
    dependencies=[Security(cookie_scheme), Depends(get_current_user)],
)
def api_riders(q: str = "", conn=Depends(get_db)):
    with conn.cursor() as cur:
        if q:
            cur.execute(
                """SELECT source, source_url, name, nationality, birth_date,
                          sanctions, team, instagram, notes, scraped_at, valid_from
                   FROM riders_current
                   WHERE name ILIKE %s
                   ORDER BY name""",
                (f"%{q}%",),
            )
        else:
            cur.execute(
                """SELECT source, source_url, name, nationality, birth_date,
                          sanctions, team, instagram, notes, scraped_at, valid_from
                   FROM riders_current
                   ORDER BY name"""
            )
        columns = [desc[0] for desc in cur.description]
        rows = []
        for row in cur.fetchall():
            d = dict(zip(columns, row))
            for key in ("scraped_at", "valid_from"):
                if d[key] is not None:
                    d[key] = d[key].isoformat()
            rows.append(d)
    return rows


@app.get(
    "/api/overrides",
    tags=["overrides"],
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


@app.get(
    "/api/overrides/{override_id}",
    tags=["overrides"],
    summary="Get override by ID",
    response_model=OverrideOut,
    dependencies=[Security(cookie_scheme), Depends(get_current_user)],
)
def api_override_detail(override_id: int, conn=Depends(get_db)):
    return _fetch_override(override_id, conn)


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


@app.post(
    "/api/overrides",
    tags=["overrides"],
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


@app.put(
    "/api/overrides/{override_id}",
    tags=["overrides"],
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


@app.delete(
    "/api/overrides/{override_id}",
    tags=["overrides"],
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


# ── Admin endpoints ──────────────────────────────────────────────────────


@app.get(
    "/api/admin/users",
    tags=["admin"],
    summary="List all users",
    response_model=List[AdminUserOut],
    dependencies=[Security(cookie_scheme), Depends(require_admin)],
)
def admin_list_users(conn=Depends(get_db)):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, email, role, created_at FROM users ORDER BY created_at"
        )
        columns = [desc[0] for desc in cur.description]
        rows = []
        for row in cur.fetchall():
            d = dict(zip(columns, row))
            if d["created_at"] is not None:
                d["created_at"] = d["created_at"].isoformat()
            rows.append(d)
    return rows


class UpdateUserBody(BaseModel):
    role: Optional[str] = None
    email: Optional[str] = None
    new_password: Optional[str] = None


@app.put(
    "/api/admin/users/{user_id}",
    tags=["admin"],
    summary="Update user",
    response_model=UserOut,
    dependencies=[Security(cookie_scheme), Depends(require_admin)],
)
def admin_update_user(user_id: int, body: UpdateUserBody, conn=Depends(get_db)):
    if not body.role and not body.email and not body.new_password:
        raise HTTPException(status_code=400, detail="At least one field must be provided")

    user = get_user_by_id(conn, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if body.email and body.email != user["email"]:
        existing = get_user_by_email(conn, body.email)
        if existing:
            raise HTTPException(status_code=409, detail="Email already taken")
        update_user_email(conn, user_id, body.email)

    if body.new_password:
        update_user_password(conn, user_id, body.new_password)

    if body.role:
        if body.role not in ("user", "admin"):
            raise HTTPException(status_code=400, detail="Role must be 'user' or 'admin'")
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET role = %s, updated_at = now() WHERE id = %s",
                (body.role, user_id),
            )
        conn.commit()

    updated = get_user_by_id(conn, user_id)
    return {"id": updated["id"], "email": updated["email"], "role": updated["role"]}


@app.delete(
    "/api/admin/users/{user_id}",
    tags=["admin"],
    summary="Delete user",
    status_code=204,
    dependencies=[Security(cookie_scheme)],
)
def admin_delete_user(user_id: int, conn=Depends(get_db), admin=Depends(require_admin)):
    if user_id == admin["id"]:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM users WHERE id = %s RETURNING id",
            (user_id,),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="User not found")
    conn.commit()


# ── SPA static files ─────────────────────────────────────────────────────

if UI_DIST.is_dir():
    app.mount("/assets", StaticFiles(directory=UI_DIST / "assets"), name="assets")

    @app.get("/{full_path:path}")
    def spa_catch_all(full_path: str):
        file = UI_DIST / full_path
        if file.is_file():
            return FileResponse(file)
        return FileResponse(UI_DIST / "index.html")
