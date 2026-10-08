import re

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import (check_password, clear, current_user, hash_password, issue, now_ms, password_problem,
                      user_id_from)
from app.db import get_db
from app.ratelimit import LOGIN, LOGIN_PER_IP, REGISTER, client_ip

router = APIRouter(prefix="/auth", tags=["auth"])

EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class Credentials(BaseModel):
    # Lengths are checked in code so the user gets a sentence, not a validation list.
    email: str = Field(max_length=200)
    password: str = Field(max_length=200)
    display_name: str | None = Field(default=None, max_length=80)


class PasswordChange(BaseModel):
    current_password: str = Field(max_length=200)
    new_password: str = Field(max_length=200)


@router.post("/guest")
def guest(response: Response, db: Session = Depends(get_db)) -> dict:
    uid = db.execute(text("INSERT INTO users (is_guest, display_name) VALUES (true, 'Guest') RETURNING id")).scalar()
    db.commit()
    issue(response, uid)
    return {"id": uid, "is_guest": True}


@router.post("/register")
def register(body: Credentials, request: Request, response: Response, db: Session = Depends(get_db)) -> dict:
    """Create an account, or upgrade the current guest (keeping everything the guest did)."""
    ip = "ip:" + client_ip(request)
    REGISTER.check(ip)
    email = body.email.strip().lower()
    if not EMAIL.match(email):
        REGISTER.fail(ip)
        raise HTTPException(422, "Enter a valid email address, like name@example.com")
    if problem := password_problem(body.password, email):
        raise HTTPException(422, problem)
    if db.execute(text("SELECT 1 FROM users WHERE email = :e"), {"e": email}).first():
        REGISTER.fail(ip)
        raise HTTPException(409, "An account with this email already exists. Sign in instead")
    pw = hash_password(body.password)
    name = (body.display_name or "").strip() or email.split("@")[0]
    uid = user_id_from(request, db)
    is_guest = uid is not None and db.execute(text("SELECT is_guest FROM users WHERE id = :u"), {"u": uid}).scalar()
    try:
        if is_guest:
            db.execute(text("UPDATE users SET email = :e, password_hash = :p, display_name = :n, is_guest = false WHERE id = :u"),
                       {"e": email, "p": pw, "n": name, "u": uid})
        else:
            uid = db.execute(text("INSERT INTO users (email, password_hash, display_name) VALUES (:e, :p, :n) RETURNING id"),
                             {"e": email, "p": pw, "n": name}).scalar()
        db.commit()
    except IntegrityError:      # two sign-ups for the same email at the same moment
        db.rollback()
        raise HTTPException(409, "An account with this email already exists. Sign in instead")
    REGISTER.fail(ip)           # every account counts toward the per-address sign-up limit
    issue(response, uid)
    return {"id": uid, "is_guest": False}


@router.post("/login")
def login(body: Credentials, request: Request, response: Response, db: Session = Depends(get_db)) -> dict:
    email = body.email.strip().lower()
    ip = "ip:" + client_ip(request)
    LOGIN.check("email:" + email, ip)
    row = db.execute(text("SELECT id, password_hash FROM users WHERE email = :e"), {"e": email}).first()
    if not row or not check_password(body.password, row[1]):
        LOGIN.fail("email:" + email)
        LOGIN.fail(ip, limit=LOGIN_PER_IP)
        raise HTTPException(401, "Wrong email or password")
    LOGIN.reset("email:" + email)
    issue(response, row[0])
    return {"id": row[0], "is_guest": False}


@router.post("/change-password")
def change_password(body: PasswordChange, response: Response, user=Depends(current_user),
                    db: Session = Depends(get_db)) -> dict:
    """New password; every other device is signed out, this one gets a fresh session."""
    if user["is_guest"]:
        raise HTTPException(403, "Guests have no password. Create an account first")
    key = "email:" + user["email"]
    LOGIN.check(key)
    hashed = db.execute(text("SELECT password_hash FROM users WHERE id = :u"), {"u": user["id"]}).scalar()
    if not check_password(body.current_password, hashed):
        LOGIN.fail(key)
        raise HTTPException(401, "Your current password is not right")
    if body.new_password == body.current_password:
        raise HTTPException(422, "Pick a new password that is different from the current one")
    if problem := password_problem(body.new_password, user["email"]):
        raise HTTPException(422, problem)
    # Strictly after this session's token, so even a token from the same millisecond is retired.
    stamp = max(now_ms(), user["token_issued_ms"] + 1)
    db.execute(text("UPDATE users SET password_hash = :p, password_changed_at = to_timestamp(:t / 1000.0) WHERE id = :u"),
               {"p": hash_password(body.new_password), "t": stamp, "u": user["id"]})
    db.commit()
    issue(response, user["id"], stamp)
    return {"ok": True}


@router.post("/logout")
def logout(response: Response) -> dict:
    clear(response)
    return {"ok": True}
