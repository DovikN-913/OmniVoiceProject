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
        """创建一个内存内限流器。

        规则：
        - QPS：按 API key 维度的 1 秒滑动窗口
        - Daily：按 API key 维度的每日计数
        """
        self._windows: dict[str, deque[float]] = defaultdict(deque)
        self._daily: dict[str, tuple[str, int]] = {}

    def check(self, api_key: str) -> RateLimitResult:
        """检查并消耗一次 API key 的限流额度。

        Args:
            api_key: 用于标识调用方的 API key。

        Returns:
            RateLimitResult，包含是否允许以及用于响应头的限流元数据。
        """
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
