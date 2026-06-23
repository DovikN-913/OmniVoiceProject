import time
from typing import Any

from app.core.config import IDEMPOTENCY_TTL_SECONDS


class IdempotencyStore:
    def __init__(self) -> None:
        self._cache: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Any | None:
        self._purge()
        item = self._cache.get(key)
        if not item:
            return None
        expires_at, value = item
        if expires_at < time.time():
            self._cache.pop(key, None)
            return None
        return value

    def set(self, key: str, value: Any) -> None:
        self._purge()
        self._cache[key] = (time.time() + IDEMPOTENCY_TTL_SECONDS, value)

    def _purge(self) -> None:
        now = time.time()
        expired = [k for k, (exp, _) in self._cache.items() if exp < now]
        for key in expired:
            self._cache.pop(key, None)


idempotency_store = IdempotencyStore()
