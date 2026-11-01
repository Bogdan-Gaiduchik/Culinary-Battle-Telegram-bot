from typing import Any

from cachetools import TTLCache


class MemoryCache:
    """Кэш в памяти с временем жизни записей (TTL)."""

    def __init__(self, maxsize: int = 512, ttl: int = 3600):
        self._data: TTLCache = TTLCache(maxsize=maxsize, ttl=ttl)

    def get(self, key: str) -> Any | None:
        return self._data.get(key)

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value
