"""Client-side rate limiting for Gemini calls.

- Sliding-window requests-per-minute per role (agent / lite / embed).
- Daily request budget per role, persisted to .cache/usage.json (survives restarts).
- call_with_retry: exponential backoff + jitter on 429/5xx, honours server retry hints.
Thread-safe. Stdlib only.
"""
import json
import random
import re
import threading
import time
from collections import deque
from datetime import date

from . import config


class DailyBudgetExceeded(RuntimeError):
    pass


class RateLimiter:
    def __init__(self, rpm, rpd, role, usage_path=None):
        self.rpm, self.rpd, self.role = max(1, rpm), rpd, role
        self.window = deque()
        self.lock = threading.Lock()
        self.path = usage_path or (config.CACHE_DIR / "usage.json")

    # --- daily budget (persisted)
    def _read(self):
        try:
            return json.loads(self.path.read_text())
        except Exception:
            return {}

    def _bump_daily(self):
        today = date.today().isoformat()
        data = self._read()
        if data.get("date") != today:
            data = {"date": today}
        used = data.get(self.role, 0)
        if self.rpd and used >= self.rpd:
            raise DailyBudgetExceeded(f"{self.role}: daily budget {self.rpd} reached")
        data[self.role] = used + 1
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(data))

    def used_today(self):
        d = self._read()
        return d.get(self.role, 0) if d.get("date") == date.today().isoformat() else 0

    # --- per-minute window
    def acquire(self):
        """Block until a request slot is free, then count it."""
        while True:
            with self.lock:
                now = time.monotonic()
                while self.window and now - self.window[0] >= 60:
                    self.window.popleft()
                if len(self.window) < self.rpm:
                    self._bump_daily()
                    self.window.append(now)
                    return
                wait = 60 - (now - self.window[0]) + 0.05
            time.sleep(max(wait, 0.05))


_limiters = {}


def limiter(role):
    if role not in _limiters:
        _limiters[role] = RateLimiter(config.RPM[role], config.RPD[role], role)
    return _limiters[role]


def _retry_after(exc):
    m = re.search(r"retry(?:Delay)?[^0-9]{0,12}(\d+(?:\.\d+)?)\s*s", str(exc), re.I)
    return float(m.group(1)) if m else None


def _retryable(exc):
    s = str(exc)
    code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
    return code in (429, 500, 502, 503, 504) or any(
        t in s for t in ("429", "RESOURCE_EXHAUSTED", "UNAVAILABLE", "503", "overloaded"))


def call_with_retry(role, fn, *args, max_tries=6, base=2.0, cap=60.0, **kwargs):
    """Run fn under the role's limiter; back off on rate-limit/transient errors."""
    lim = limiter(role)
    for attempt in range(max_tries):
        lim.acquire()
        try:
            return fn(*args, **kwargs)
        except DailyBudgetExceeded:
            raise
        except Exception as e:  # noqa: BLE001
            if attempt == max_tries - 1 or not _retryable(e):
                raise
            hint = _retry_after(e)
            delay = hint if hint is not None else min(cap, base ** attempt)
            time.sleep(delay + random.uniform(0, 0.5))
