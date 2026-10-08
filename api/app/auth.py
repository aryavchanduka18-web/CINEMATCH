"""Auth: JWT in an httpOnly cookie (spec section 11). Guests are real database users with is_guest."""
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException, Request, Response
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db

COOKIE = "cm_session"
MAX_AGE = 60 * 60 * 24 * 30          # 30 days


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def check_password(password: str, hashed: str | None) -> bool:
    return bool(hashed) and bcrypt.checkpw(password.encode(), hashed.encode())


def _secret() -> str:
    secret = get_settings().jwt_secret
    if not secret:
        raise RuntimeError("JWT_SECRET is not set in .env")
    return secret


def issue(response: Response, user_id: int) -> None:
    token = jwt.encode({"sub": str(user_id), "exp": datetime.now(timezone.utc) + timedelta(seconds=MAX_AGE)},
                       _secret(), algorithm="HS256")
    response.set_cookie(COOKIE, token, max_age=MAX_AGE, httponly=True, samesite="lax", secure=False, path="/")


def clear(response: Response) -> None:
    response.delete_cookie(COOKIE, path="/")


def user_id_from(request: Request) -> int | None:
    token = request.cookies.get(COOKIE)
    if not token:
        return None
    try:
        return int(jwt.decode(token, _secret(), algorithms=["HS256"])["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        return None


def current_user(request: Request, db: Session = Depends(get_db)) -> dict:
    uid = user_id_from(request)
    if uid is None:
        raise HTTPException(401, "Not signed in")
    row = db.execute(text("SELECT id, email, display_name, is_guest, onboarded_at FROM users WHERE id = :u"),
                     {"u": uid}).mappings().first()
    if row is None:
        raise HTTPException(401, "Unknown user")
    return dict(row)