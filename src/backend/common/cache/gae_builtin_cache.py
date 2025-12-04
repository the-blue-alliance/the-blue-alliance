from __future__ import annotations

from collections.abc import Generator
from typing import Any

from google.appengine.api import memcache

from backend.common.cache.cache_if import CacheIf, CacheStats
from backend.common.tasklets import typed_tasklet


class AppEngineBuiltinCache(CacheIf):
    """
    A cache implementation using builtin memcache
    """

    memcache_client: memcache.Client

    def __init__(self, memcache_client: memcache.Client) -> None:
        self.memcache_client = memcache_client

    def set(self, key: bytes, value: Any, time: int | None = None) -> bool:
        return self.memcache_client.set(key, value, time or 0)

    @typed_tasklet
    def set_async(
        self, key: bytes, value: Any, time: int | None = None
    ) -> Generator[Any, Any, bool]:
        status_dict = yield self.memcache_client.set_multi_async(
            {key: value}, time or 0
        )
        return (
            status_dict and status_dict.get(key) == memcache.MemcacheSetResponse.STORED
        )

    def set_multi(
        self,
        mapping: dict[bytes, Any],
        time: int | None = None,
        namespace: str | None = None,
    ) -> None:
        self.memcache_client.set_multi(mapping, time=(time or 0), namespace=namespace)

    def get(self, key: bytes) -> Any | None:
        return self.memcache_client.get(key)

    @typed_tasklet
    def get_async(self, key: bytes) -> Generator[Any, Any, Any]:
        results = yield self.memcache_client.get_multi_async([key])
        return results.get(key)

    def get_multi(
        self, keys: list[bytes], namespace: str | None = None
    ) -> dict[bytes, Any | None]:
        return self.memcache_client.get_multi(keys, namespace=namespace)

    def delete(self, key: bytes) -> None:
        self.memcache_client.delete(key)

    def delete_multi(self, keys: list[bytes]) -> None:
        self.memcache_client.delete_multi(keys)

    def incr(self, key: bytes) -> int | None:
        return self.memcache_client.incr(key)

    def decr(self, key: bytes) -> int | None:
        return self.memcache_client.decr(key)

    def get_stats(self) -> CacheStats | None:
        return self.memcache_client.get_stats()
