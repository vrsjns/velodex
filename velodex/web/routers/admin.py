from typing import List, Optional

from fastapi import Depends, HTTPException, Security
from fastapi.routing import APIRouter
from pydantic import BaseModel

from velodex.web.auth import (
    get_user_by_email,
    get_user_by_id,
    require_admin,
    update_user_email,
    update_user_password,
)
from velodex.web.deps import cookie_scheme, get_db
from velodex.web.routers.auth import UserOut

router = APIRouter(prefix="/api/admin", tags=["admin"])


class AdminUserOut(BaseModel):
    id: int
    email: str
    role: str
    created_at: Optional[str] = None


class UpdateUserBody(BaseModel):
    role: Optional[str] = None
    email: Optional[str] = None
    new_password: Optional[str] = None


@router.get(
    "/users",
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


@router.put(
    "/users/{user_id}",
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


@router.delete(
    "/users/{user_id}",
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
