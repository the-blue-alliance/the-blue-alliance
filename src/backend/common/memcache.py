from __future__ import annotations

from typing import Optional

from pyre_extensions import none_throws

from backend.common.cache.cache_if import CacheIf
from backend.common.cache.noop_cache import NoopCache
from backend.common.cache.redis_cache import RedisCache
from backend.common.redis import RedisClient


class MemcacheClient:

    _cache: Optional[CacheIf] = None

    @classmethod
    def get(cls) -> CacheIf:
        if cls._cache is None:
            redis_client = RedisClient.get()
            if redis_client is not None:
                cls._cache = RedisCache(redis_client)
            else:
                cls._cache = NoopCache()

        return none_throws(cls._cache)

    @classmethod
    def reset(cls) -> None:
        cls._cache = None
