"""In-memory failure counter with lockout, for sign-in and sign-up.

Kept in process memory: CineMatch runs as one web process, so one counter is enough. A restart
clears it, which is acceptable for a project of this size (see docs/decisions-log.md).
"""
import math
import time
from collections import deque
from threading import Lock

from fastapi import HTTPException


class Limiter:
    def __init__(self, max_failures: int, window_s: int, lockout_s: int, what: str):
        self.max_failures, self.window_s, self.lockout_s, self.what = max_failures, window_s, lockout_s, what
        self._fails: dict[str, deque[float]] = {}
        self._locked_until: dict[str, float] = {}
        self._lock = Lock()

    def check(self, *keys: str) -> None:
        """Raise 429 with a clear message if any of the keys is locked out."""
        now = time.monotonic()
        with self._lock:
            wait = max((self._locked_until.get(k, 0) - now for k in keys), default=0)
        if wait > 0:
            minutes = max(1, math.ceil(wait / 60))
            raise HTTPException(429, f"Too many {self.what}. Try again in {minutes} minute{'s' if minutes > 1 else ''}.",
                                headers={"Retry-After": str(math.ceil(wait))})

    def fail(self, key: str, limit: int | None = None) -> None:
        now = time.monotonic()
        with self._lock:
            q = self._fails.setdefault(key, deque())
            q.append(now)
            while q and q[0] < now - self.window_s:
                q.popleft()
            if len(q) >= (limit or self.max_failures):
                self._locked_until[key] = now + self.lockout_s
                q.clear()

    def reset(self, key: str) -> None:
        with self._lock:
            self._fails.pop(key, None)
            self._locked_until.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._fails.clear()
            self._locked_until.clear()


# 5 wrong passwords for one email (or 20 from one address) within 15 minutes lock it for 15 minutes.
LOGIN = Limiter(max_failures=5, window_s=15 * 60, lockout_s=15 * 60, what="sign-in attempts")
LOGIN_PER_IP = 20
# 10 accounts (or failed sign-ups) from one address within an hour pause sign-up for an hour.
REGISTER = Limiter(max_failures=10, window_s=60 * 60, lockout_s=60 * 60, what="sign-up attempts")


def client_ip(request) -> str:
    # Behind one proxy (Render) the last X-Forwarded-For entry is the address the proxy saw;
    # earlier entries come from the visitor and could be made up.
    fwd = request.headers.get("x-forwarded-for", "")
    return fwd.split(",")[-1].strip() or (request.client.host if request.client else "unknown")
