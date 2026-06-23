import time
from collections import defaultdict, deque
from dataclasses import dataclass

from app.core.config import RATE_LIMIT_DAILY, RATE_LIMIT_QPS


@dataclass
class RateLimitResult:
    allowed: bool
    limit: int
    remaining: int
    reset_at: int
    retry_after: int


class RateLimiter:
    def __init__(self) -> None:
        self._windows: dict[str, deque[float]] = defaultdict(deque)
        self._daily: dict[str, tuple[str, int]] = {}

    def check(self, api_key: str) -> RateLimitResult:
        now = time.time()
        window = self._windows[api_key]
        while window and now - window[0] >= 1.0:
            window.popleft()

        day_key = time.strftime("%Y-%m-%d", time.localtime(now))
        stored_day, count = self._daily.get(api_key, (day_key, 0))
        if stored_day != day_key:
            stored_day, count = day_key, 0

        reset_at = int(now) + 1
        retry_after = max(1, reset_at - int(now))

        if count >= RATE_LIMIT_DAILY:
            return RateLimitResult(False, RATE_LIMIT_QPS, 0, reset_at, retry_after)
        if len(window) >= RATE_LIMIT_QPS:
            return RateLimitResult(False, RATE_LIMIT_QPS, 0, reset_at, retry_after)

        window.append(now)
        self._daily[api_key] = (stored_day, count + 1)
        remaining = max(0, RATE_LIMIT_QPS - len(window))
        return RateLimitResult(True, RATE_LIMIT_QPS, remaining, reset_at, retry_after)


rate_limiter = RateLimiter()
