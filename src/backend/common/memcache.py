from __future__ import annotations

from typing import Optional

from google.appengine.api import memcache
from pyre_extensions import none_throws

from backend.common.cache.cache_if import CacheIf
from backend.common.cache.gae_builtin_cache import AppEngineBuiltinCache


class MemcacheClient:
    _cache: Optional[CacheIf] = None

    @classmethod
    def get(cls) -> CacheIf:
        if cls._cache is None:
            cls._cache = AppEngineBuiltinCache(memcache.Client())
        return none_throws(cls._cache)

    @classmethod
    def reset(cls) -> None:
        cls._cache = None
