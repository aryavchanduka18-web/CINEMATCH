from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.auth import check_password, clear, hash_password, issue, user_id_from
from app.db import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


class Credentials(BaseModel):
    email: str = Field(min_length=3, max_length=200)
    password: str = Field(min_length=8, max_length=200)
    display_name: str | None = Field(default=None, max_length=80)


@router.post("/guest")
def guest(response: Response, db: Session = Depends(get_db)) -> dict:
    uid = db.execute(text("INSERT INTO users (is_guest, display_name) VALUES (true, 'Guest') RETURNING id")).scalar()
    db.commit()
    issue(response, uid)
    return {"id": uid, "is_guest": True}


@router.post("/register")
def register(body: Credentials, request: Request, response: Response, db: Session = Depends(get_db)) -> dict:
    """Create an account, or upgrade the current guest (keeping everything the guest did)."""
    email = body.email.strip().lower()
    if "@" not in email:
        raise HTTPException(422, "Enter a valid email address")
    if db.execute(text("SELECT 1 FROM users WHERE email = :e"), {"e": email}).first():
        raise HTTPException(409, "An account with this email already exists")
    pw = hash_password(body.password)
    name = body.display_name or email.split("@")[0]
    uid = user_id_from(request)
    is_guest = uid is not None and db.execute(text("SELECT is_guest FROM users WHERE id = :u"), {"u": uid}).scalar()
    if is_guest:
        db.execute(text("UPDATE users SET email = :e, password_hash = :p, display_name = :n, is_guest = false WHERE id = :u"),
                   {"e": email, "p": pw, "n": name, "u": uid})
    else:
        uid = db.execute(text("INSERT INTO users (email, password_hash, display_name) VALUES (:e, :p, :n) RETURNING id"),
                         {"e": email, "p": pw, "n": name}).scalar()
    db.commit()
    issue(response, uid)
    return {"id": uid, "is_guest": False}


@router.post("/login")
def login(body: Credentials, response: Response, db: Session = Depends(get_db)) -> dict:
    row = db.execute(text("SELECT id, password_hash FROM users WHERE email = :e"), {"e": body.email.strip().lower()}).first()
    if not row or not check_password(body.password, row[1]):
        raise HTTPException(401, "Wrong email or password")
    issue(response, row[0])
    return {"id": row[0], "is_guest": False}


@router.post("/logout")
def logout(response: Response) -> dict:
    clear(response)
    return {"ok": True}