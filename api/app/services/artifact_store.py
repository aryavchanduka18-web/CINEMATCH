"""Model artifacts for a hosted copy, delivered through the (private) database.

The repository is public and the artifacts are built from MovieLens ratings, which may not be
redistributed, so they are never committed. Instead scripts/deploy_data.py uploads one compact
bundle (artifacts.tar.gz: models/, metrics/, lab/) into the table deploy_artifacts of the hosted
database, and the server unpacks it into artifacts/ when it starts, or on first use if the upload
happened after the server started.

Run at container start:  python -m app.services.artifact_store
"""
import hashlib
import io
import logging
import tarfile
import threading
import time
from pathlib import Path

from sqlalchemy import text

log = logging.getLogger("uvicorn.error")

ROOT = Path(__file__).resolve().parents[3] / "artifacts"
BUNDLE = "artifacts.tar.gz"
MARKER = ROOT / ".bundle_sha256"
TABLE_SQL = """CREATE TABLE IF NOT EXISTS deploy_artifacts (
    name text PRIMARY KEY, sha256 text NOT NULL, data bytea NOT NULL, uploaded_at timestamptz NOT NULL DEFAULT now())"""

_lock = threading.Lock()
_last_try = 0.0
RETRY_S = 30


def _extract(data: bytes) -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tar:
        tar.extractall(ROOT, filter="data")      # "data" refuses absolute paths, links out and ../


def sync(force: bool = False) -> bool:
    """Unpack the uploaded bundle if it is newer than what is on disk. True if something was unpacked."""
    from app.db import engine
    with engine.connect() as conn:
        if conn.execute(text("SELECT to_regclass('deploy_artifacts')")).scalar() is None:
            return False
        row = conn.execute(text("SELECT sha256, data FROM deploy_artifacts WHERE name = :n"), {"n": BUNDLE}).first()
    if row is None:
        return False
    sha, data = row[0], bytes(row[1])
    if not force and MARKER.exists() and MARKER.read_text().strip() == sha:
        return False
    if hashlib.sha256(data).hexdigest() != sha:
        log.error("artifact bundle checksum mismatch; not unpacking")
        return False
    _extract(data)
    MARKER.write_text(sha)
    log.info("unpacked artifact bundle %s (%.1f MB)", sha[:12], len(data) / 1e6)
    return True


def try_sync() -> None:
    """Called when artifacts are missing; checks the database at most every RETRY_S seconds."""
    global _last_try
    with _lock:
        if time.monotonic() - _last_try < RETRY_S:
            return
        _last_try = time.monotonic()
        try:
            sync()
        except Exception:      # a missing bundle must never take the site down
            log.exception("could not fetch the artifact bundle")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("artifact bundle unpacked" if sync() else "artifact bundle: nothing new to unpack")
