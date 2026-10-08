"""Accounts: sign-up rules, sign-in lockout, password change signing out other sessions, deletion."""
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.auth import COOKIE
from app.config import get_settings
from app.main import app
from app.ratelimit import LOGIN, REGISTER

GOOD = "popcorn42night"


@pytest.fixture(autouse=True)
def fresh_limits():
    LOGIN.clear()
    REGISTER.clear()
    yield
    LOGIN.clear()
    REGISTER.clear()


def email() -> str:
    return f"u{uuid.uuid4().hex[:10]}@example.com"


def client() -> TestClient:
    return TestClient(app)


def register(c: TestClient, e: str, pw: str = GOOD):
    return c.post("/api/auth/register", json={"email": e, "password": pw, "display_name": "Test"})


@pytest.mark.parametrize("pw, message", [
    ("short1", "at least 8 characters"),
    ("onlyletters", "one letter and one number"),
    ("12345678901", "one letter and one number"),
    ("password1", "too common"),
])
def test_register_rejects_weak_passwords_with_a_clear_sentence(pw, message):
    res = register(client(), email(), pw)
    assert res.status_code == 422
    assert message in res.json()["detail"]


def test_register_rejects_bad_email_and_duplicates():
    c = client()
    assert register(c, "not-an-email").json()["detail"].startswith("Enter a valid email address")
    e = email()
    assert register(c, e).status_code == 200
    dup = register(client(), e.upper())
    assert dup.status_code == 409 and "already exists" in dup.json()["detail"]


def test_guest_upgrade_keeps_the_same_user():
    c = client()
    gid = c.post("/api/auth/guest").json()["id"]
    assert register(c, email()).json()["id"] == gid
    assert c.get("/api/me").json()["is_guest"] is False


def test_login_locks_after_five_wrong_passwords():
    e = email()
    register(client(), e)
    c = client()
    for _ in range(5):
        assert c.post("/api/auth/login", json={"email": e, "password": "wrong-pass-1"}).status_code == 401
    locked = c.post("/api/auth/login", json={"email": e, "password": GOOD})   # even the right one is refused now
    assert locked.status_code == 429
    assert "Try again in 15 minutes" in locked.json()["detail"]
    assert int(locked.headers["retry-after"]) > 0


def test_successful_login_resets_the_counter():
    e = email()
    register(client(), e)
    c = client()
    for _ in range(2):
        for _ in range(4):
            c.post("/api/auth/login", json={"email": e, "password": "wrong-pass-1"})
        assert c.post("/api/auth/login", json={"email": e, "password": GOOD}).status_code == 200


def test_register_is_rate_limited_per_address():
    c = client()
    codes = [register(c, email()).status_code for _ in range(11)]
    assert codes[:10] == [200] * 10 and codes[10] == 429


def test_change_password_signs_out_other_sessions_only():
    e = email()
    laptop, phone = client(), client()
    register(laptop, e)
    assert phone.post("/api/auth/login", json={"email": e, "password": GOOD}).status_code == 200
    wrong = laptop.post("/api/auth/change-password", json={"current_password": "nope-123x", "new_password": "fresh99reel"})
    assert wrong.status_code == 401
    ok = laptop.post("/api/auth/change-password", json={"current_password": GOOD, "new_password": "fresh99reel"})
    assert ok.status_code == 200
    assert laptop.get("/api/me").status_code == 200                # this device got a new cookie
    assert phone.get("/api/me").status_code == 401                 # the other device is signed out
    assert client().post("/api/auth/login", json={"email": e, "password": GOOD}).status_code == 401
    assert client().post("/api/auth/login", json={"email": e, "password": "fresh99reel"}).status_code == 200


def test_change_password_applies_the_rules():
    c = client()
    register(c, email())
    res = c.post("/api/auth/change-password", json={"current_password": GOOD, "new_password": GOOD})
    assert res.status_code == 422 and "different" in res.json()["detail"]
    res = c.post("/api/auth/change-password", json={"current_password": GOOD, "new_password": "abcdefgh"})
    assert res.status_code == 422


def test_guest_cannot_change_password():
    c = client()
    c.post("/api/auth/guest")
    assert c.post("/api/auth/change-password", json={"current_password": "", "new_password": "fresh99reel"}).status_code == 403


def test_rename_account():
    c = client()
    register(c, email())
    assert c.patch("/api/me", json={"display_name": "  Aryav  "}).json()["display_name"] == "Aryav"
    assert c.get("/api/me").json()["display_name"] == "Aryav"
    assert c.patch("/api/me", json={"display_name": "   "}).status_code == 422


def test_delete_account_needs_the_password_and_removes_everything(test_engine):
    c = client()
    uid = register(c, email()).json()["id"]
    with test_engine.begin() as conn:
        mid = conn.execute(text("INSERT INTO movies (tmdb_id, title) VALUES (-77, 'Del') RETURNING id")).scalar()
    try:
        assert c.put(f"/api/ratings/{mid}", json={"rating": 8}).status_code == 200
        assert c.request("DELETE", "/api/me", json={"password": "wrong-pass-1"}).status_code == 403
        assert c.request("DELETE", "/api/me", json={"password": GOOD}).json() == {"deleted": True}
        with test_engine.connect() as conn:
            left = conn.execute(text("""SELECT (SELECT count(*) FROM users WHERE id = :u)
                + (SELECT count(*) FROM ratings WHERE user_id = :u)
                + (SELECT count(*) FROM interactions WHERE user_id = :u)"""), {"u": uid}).scalar()
        assert left == 0
    finally:
        with test_engine.begin() as conn:
            conn.execute(text("DELETE FROM movies WHERE id = :m"), {"m": mid})


def test_guest_can_delete_without_a_password():
    c = client()
    c.post("/api/auth/guest")
    assert c.request("DELETE", "/api/me", json={}).json() == {"deleted": True}
    assert c.get("/api/me").status_code == 401


def test_secure_cookie_follows_settings(monkeypatch):
    monkeypatch.setattr(get_settings(), "cookie_secure", True)
    header = client().post("/api/auth/guest").headers["set-cookie"].lower()
    assert "secure" in header and "httponly" in header and "samesite=lax" in header
