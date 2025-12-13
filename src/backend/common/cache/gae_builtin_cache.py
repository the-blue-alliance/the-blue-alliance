from __future__ import annotations

from typing import Any, Dict, Generator, List, Optional

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

    def set(self, key: bytes, value: Any, time: Optional[int] = None) -> bool:
        return self.memcache_client.set(key, value, time or 0)

    @typed_tasklet
    def set_async(
        self, key: bytes, value: Any, time: Optional[int] = None
    ) -> Generator[Any, Any, bool]:
        status_dict = yield self.memcache_client.set_multi_async(
            {key: value}, time or 0
        )
        return (
            status_dict and status_dict.get(key) == memcache.MemcacheSetResponse.STORED
        )

    def set_multi(
        self,
        mapping: Dict[bytes, Any],
        time: Optional[int] = None,
        namespace: Optional[str] = None,
    ) -> None:
        self.memcache_client.set_multi(mapping, time=(time or 0), namespace=namespace)

    def get(self, key: bytes) -> Optional[Any]:
        return self.memcache_client.get(key)

    @typed_tasklet
    def get_async(self, key: bytes) -> Generator[Any, Any, Any]:
        results = yield self.memcache_client.get_multi_async([key])
        return results.get(key)

    def get_multi(
        self, keys: List[bytes], namespace: Optional[str] = None
    ) -> Dict[bytes, Optional[Any]]:
        return self.memcache_client.get_multi(keys, namespace=namespace)

    def delete(self, key: bytes) -> None:
        self.memcache_client.delete(key)

    def delete_multi(self, keys: List[bytes]) -> None:
        self.memcache_client.delete_multi(keys)

    def incr(self, key: bytes) -> Optional[int]:
        return self.memcache_client.incr(key)

    def decr(self, key: bytes) -> Optional[int]:
        return self.memcache_client.decr(key)

    def get_stats(self) -> Optional[CacheStats]:
        return self.memcache_client.get_stats()
