from typing import Optional

from fastapi import Cookie, Depends, HTTPException, Response, Security
from fastapi.routing import APIRouter
from pydantic import BaseModel

from velodex.web.auth import (
    clear_auth_cookies,
    create_user,
    decode_token,
    get_current_user,
    get_user_by_email,
    get_user_by_id,
    get_user_with_password,
    set_auth_cookies,
    update_user_email,
    update_user_password,
    verify_password,
)
from velodex.web.deps import cookie_scheme, get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])


class UserOut(BaseModel):
    id: int
    email: str
    role: str


class AuthBody(BaseModel):
    email: str
    password: str


class ProfileBody(BaseModel):
    email: Optional[str] = None
    current_password: Optional[str] = None
    new_password: Optional[str] = None


@router.post(
    "/register",
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


@router.post(
    "/login",
    summary="Log in",
    response_model=UserOut,
)
def auth_login(body: AuthBody, response: Response, conn=Depends(get_db)):
    user = get_user_by_email(conn, body.email)
    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    set_auth_cookies(response, user["id"], user["role"])
    return {"id": user["id"], "email": user["email"], "role": user["role"]}


@router.post(
    "/logout",
    summary="Log out",
)
def auth_logout(response: Response):
    clear_auth_cookies(response)
    return {"ok": True}


@router.get(
    "/me",
    summary="Get current user",
    response_model=UserOut,
    dependencies=[Security(cookie_scheme)],
)
def auth_me(user=Depends(get_current_user)):
    return {"id": user["id"], "email": user["email"], "role": user["role"]}


@router.post(
    "/refresh",
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


@router.put(
    "/profile",
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
