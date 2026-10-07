"""Small TMDB API client: Bearer token from .env, rate limit, retries, on-disk cache."""
import json
import threading
import time
from pathlib import Path

import httpx

from pipeline.common import env, get_logger

API = "https://api.themoviedb.org/3"
IMG = "https://image.tmdb.org/t/p"
log = get_logger("tmdb")


class RateLimiter:
    """Allow at most `rate` calls per second across threads."""

    def __init__(self, rate: float):
        self.interval = 1.0 / rate
        self.lock = threading.Lock()
        self.next_at = 0.0

    def wait(self) -> None:
        with self.lock:
            now = time.monotonic()
            delay = self.next_at - now
            self.next_at = max(now, self.next_at) + self.interval
        if delay > 0:
            time.sleep(delay)


class TMDB:
    def __init__(self, rate: float = 18.0):
        token = env("TMDB_API_KEY")
        if not token:
            raise RuntimeError("TMDB_API_KEY is empty in .env")
        # The long read-access token goes in a Bearer header; a short v3 key goes in the query.
        if token.startswith("eyJ"):
            headers, self.params = {"Authorization": f"Bearer {token}"}, {}
        else:
            headers, self.params = {}, {"api_key": token}
        headers["accept"] = "application/json"
        self.client = httpx.Client(base_url=API, headers=headers, timeout=30)
        self.limiter = RateLimiter(rate)

    def get(self, path: str, **params) -> dict | None:
        """GET with retries on 429/5xx/network errors. Returns None on 404."""
        for attempt in range(8):
            self.limiter.wait()
            try:
                r = self.client.get(path, params={**self.params, **params})
            except httpx.TransportError:
                time.sleep(2 ** attempt)
                continue
            if r.status_code == 200:
                return r.json()
            if r.status_code == 404:
                return None
            if r.status_code == 429 or r.status_code >= 500:
                wait = float(r.headers.get("retry-after", 2 ** attempt))
                time.sleep(min(wait, 60))
                continue
            raise RuntimeError(f"TMDB {path} -> HTTP {r.status_code}")
        raise RuntimeError(f"TMDB {path}: gave up after retries")

    def cached(self, cache_file: Path, path: str, **params) -> dict | None:
        """Return the cached JSON if present, else fetch and cache it (404s are cached too)."""
        if cache_file.exists():
            data = json.loads(cache_file.read_text(encoding="utf-8"))
            return None if data.get("_status") == 404 else data
        data = self.get(path, **params)
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        tmp = cache_file.with_suffix(".tmp")
        tmp.write_text(json.dumps(data if data is not None else {"_status": 404}), encoding="utf-8")
        tmp.replace(cache_file)
        return data

    def download_image(self, size: str, file_path: str, dest: Path) -> Path | None:
        if dest.exists():
            return dest
        for attempt in range(5):
            self.limiter.wait()
            try:
                r = httpx.get(f"{IMG}/{size}{file_path}", timeout=30)
            except httpx.TransportError:
                time.sleep(2 ** attempt)
                continue
            if r.status_code == 200:
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(r.content)
                return dest
            if r.status_code == 404:
                return None
            time.sleep(2 ** attempt)
        return None