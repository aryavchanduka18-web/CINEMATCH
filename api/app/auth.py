"""Auth: JWT in an httpOnly cookie (spec section 11). Guests are real database users with is_guest.

Each token carries the time it was issued in milliseconds (`iat_ms`). Changing the password stamps
users.password_changed_at, and any token issued before that moment stops working, so other
devices are signed out while the device that made the change gets a fresh cookie.
"""
import re
import time
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

COMMON_PASSWORDS = {"password", "password1", "password123", "12345678", "123456789", "1234567890", "qwerty123",
                    "qwertyuiop", "iloveyou1", "letmein1", "welcome1", "abc12345", "11111111", "cinematch1"}


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def check_password(password: str, hashed: str | None) -> bool:
    if not hashed or len(password.encode()) > 72:
        return False
    return bcrypt.checkpw(password.encode(), hashed.encode())


def password_problem(password: str, email: str | None = None) -> str | None:
    """The first rule a new password breaks, as a sentence for the user, or None if it is fine."""
    if len(password) < 8:
        return "Use at least 8 characters for your password"
    if len(password.encode()) > 72:
        return "Use at most 72 characters for your password"
    if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        return "Use at least one letter and one number in your password"
    if password.lower() in COMMON_PASSWORDS:
        return "That password is too common. Pick something less guessable"
    local = (email or "").split("@")[0].lower()
    if len(local) >= 4 and local in password.lower():
        return "Your password should not contain your email name"
    return None


def _secret() -> str:
    secret = get_settings().jwt_secret
    if not secret:
        raise RuntimeError("JWT_SECRET is not set in .env")
    return secret


def now_ms() -> int:
    return int(time.time() * 1000)


def issue(response: Response, user_id: int, issued_ms: int | None = None) -> None:
    s = get_settings()
    issued_ms = issued_ms or now_ms()
    token = jwt.encode({"sub": str(user_id), "iat_ms": issued_ms,
                        "exp": datetime.now(timezone.utc) + timedelta(seconds=MAX_AGE)}, _secret(), algorithm="HS256")
    response.set_cookie(COOKIE, token, max_age=MAX_AGE, httponly=True, samesite=s.cookie_samesite,
                        secure=s.cookie_secure, path="/")


def clear(response: Response) -> None:
    s = get_settings()
    response.delete_cookie(COOKIE, path="/", httponly=True, samesite=s.cookie_samesite, secure=s.cookie_secure)


def token_claims(request: Request) -> tuple[int, int] | None:
    """(user id, issued at in ms) from a valid signature, before checking it against the database."""
    token = request.cookies.get(COOKIE)
    if not token:
        return None
    try:
        claims = jwt.decode(token, _secret(), algorithms=["HS256"])
        return int(claims["sub"]), int(claims.get("iat_ms", 0))
    except (jwt.PyJWTError, KeyError, ValueError, TypeError):
        return None


def _still_valid(changed_at: datetime | None, issued_ms: int) -> bool:
    return changed_at is None or issued_ms >= round(changed_at.timestamp() * 1000)


def user_id_from(request: Request, db: Session) -> int | None:
    """The signed-in user, or None (also for a deleted user or a token from before a password change)."""
    claims = token_claims(request)
    if claims is None:
        return None
    row = db.execute(text("SELECT password_changed_at FROM users WHERE id = :u"), {"u": claims[0]}).first()
    return claims[0] if row is not None and _still_valid(row[0], claims[1]) else None


def current_user(request: Request, db: Session = Depends(get_db)) -> dict:
    claims = token_claims(request)
    if claims is None:
        raise HTTPException(401, "Not signed in")
    row = db.execute(text("""SELECT id, email, display_name, is_guest, onboarded_at, created_at, password_changed_at
                             FROM users WHERE id = :u"""), {"u": claims[0]}).mappings().first()
    if row is None or not _still_valid(row["password_changed_at"], claims[1]):
        raise HTTPException(401, "Your session has ended. Please sign in again")
    user = dict(row)
    user["token_issued_ms"] = claims[1]
    del user["password_changed_at"]
    return user
