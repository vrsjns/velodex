import os
from datetime import datetime, timedelta, timezone

from typing import Optional

import bcrypt
import jwt
from fastapi import Cookie, Depends, HTTPException, Response

from velodex.web.deps import get_db

JWT_SECRET = os.environ.get("JWT_SECRET", "dev-secret-change-in-production-env")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def create_access_token(user_id: int, role: str) -> str:
    payload = {
        "sub": str(user_id),
        "role": role,
        "type": "access",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_refresh_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "exp": datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def set_auth_cookies(response: Response, user_id: int, role: str):
    access = create_access_token(user_id, role)
    refresh = create_refresh_token(user_id)
    response.set_cookie(
        "access_token", access,
        httponly=True, samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    response.set_cookie(
        "refresh_token", refresh,
        httponly=True, samesite="lax",
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 86400,
    )


def clear_auth_cookies(response: Response):
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")


def get_user_by_email(conn, email: str):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, email, password_hash, role FROM users WHERE email = %s",
            (email,),
        )
        row = cur.fetchone()
    if not row:
        return None
    return {"id": row[0], "email": row[1], "password_hash": row[2], "role": row[3]}


def get_user_by_id(conn, user_id: int):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, email, role FROM users WHERE id = %s",
            (user_id,),
        )
        row = cur.fetchone()
    if not row:
        return None
    return {"id": row[0], "email": row[1], "role": row[2]}


def get_user_with_password(conn, user_id: int):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, email, role, password_hash FROM users WHERE id = %s",
            (user_id,),
        )
        row = cur.fetchone()
    if not row:
        return None
    return {"id": row[0], "email": row[1], "role": row[2], "password_hash": row[3]}


def update_user_email(conn, user_id: int, new_email: str):
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE users SET email = %s, updated_at = now() WHERE id = %s",
            (new_email, user_id),
        )
    conn.commit()


def update_user_password(conn, user_id: int, new_password: str):
    pw_hash = hash_password(new_password)
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE users SET password_hash = %s, updated_at = now() WHERE id = %s",
            (pw_hash, user_id),
        )
    conn.commit()


def create_user(conn, email: str, password: str, role: str = "user"):
    pw_hash = hash_password(password)
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO users (email, password_hash, role) VALUES (%s, %s, %s) RETURNING id",
            (email, pw_hash, role),
        )
        user_id = cur.fetchone()[0]
    conn.commit()
    return {"id": user_id, "email": email, "role": role}


def get_current_user(
    access_token: Optional[str] = Cookie(None),
    conn=Depends(get_db),
):
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = decode_token(access_token)
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token type")
    user = get_user_by_id(conn, int(payload["sub"]))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def require_admin(user=Depends(get_current_user)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
