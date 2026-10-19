"""Lab: another user's top picks and taste are private; only the owner or the demo account may look."""
import uuid

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.main import app
from app.routers.lab import DEMO_EMAIL, allow_user_view
from app.db import get_db


def _signed_in(c: TestClient) -> int:
    e = f"u{uuid.uuid4().hex[:10]}@example.com"
    res = c.post("/api/auth/register", json={"email": e, "password": "popcorn42night", "display_name": "Test"})
    assert res.status_code in (200, 201)
    return c.get("/api/me").json()["id"]


def test_other_users_and_signed_out_visitors_are_refused():
    owner, other = TestClient(app), TestClient(app)
    owner_id = _signed_in(owner)
    assert other.get(f"/api/lab/user/{owner_id}/candidates").status_code == 403
    assert other.get(f"/api/lab/taste-map?user_id={owner_id}").status_code == 403
    _signed_in(other)
    assert other.get(f"/api/lab/user/{owner_id}/candidates").status_code == 403
    assert other.get(f"/api/lab/taste-map?user_id={owner_id}").status_code == 403


def test_owner_and_demo_account_pass_the_access_check():
    c = TestClient(app)
    uid = _signed_in(c)
    db = next(app.dependency_overrides.get(get_db, get_db)())
    try:
        from starlette.requests import Request
        scope = {"type": "http", "headers": [(b"cookie", "; ".join(f"{k}={v}" for k, v in c.cookies.items()).encode())]}
        allow_user_view(Request(scope), db, uid)
        demo = db.execute(text("SELECT id FROM users WHERE email = :e"), {"e": DEMO_EMAIL}).scalar()
        if demo is None:
            demo = db.execute(text("""INSERT INTO users (email, display_name, password_hash, is_guest) VALUES (:e, 'Demo', 'x', false)
                                      RETURNING id"""), {"e": DEMO_EMAIL}).scalar()
            db.commit()
        allow_user_view(Request({"type": "http", "headers": []}), db, demo)
        with pytest.raises(HTTPException):
            allow_user_view(Request({"type": "http", "headers": []}), db, uid)
    finally:
        db.close()
