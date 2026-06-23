import time
from typing import Any

from app.core.config import IDEMPOTENCY_TTL_SECONDS


class IdempotencyStore:
    def __init__(self) -> None:
        """创建一个带 TTL 过期淘汰的内存幂等缓存。"""
        self._cache: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Any | None:
        """读取幂等键对应的缓存值（若未过期）。

        Args:
            key: 缓存 key（通常由 api_key 与 idempotency_key 组合得到）。

        Returns:
            命中且未过期返回缓存值，否则返回 None。
        """
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
        """写入幂等键对应的缓存值，并设置 TTL。

        Args:
            key: 缓存 key（通常由 api_key 与 idempotency_key 组合得到）。
            value: 需要复用的响应对象（通常可 JSON 序列化）。
        """
        self._purge()
        self._cache[key] = (time.time() + IDEMPOTENCY_TTL_SECONDS, value)

    def _purge(self) -> None:
        """清理过期缓存项。"""
        now = time.time()
        expired = [k for k, (exp, _) in self._cache.items() if exp < now]
        for key in expired:
            self._cache.pop(key, None)


idempotency_store = IdempotencyStore()
