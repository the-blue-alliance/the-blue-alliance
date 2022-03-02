from __future__ import annotations

from typing import Any, Dict, List, Optional

from google.appengine.api import memcache

from backend.common.cache.cache_if import CacheIf, CacheStats


class AppEngineBuiltinCache(CacheIf):
    """
    A cache implementation using builtin memcache
    """

    memcache_client: memcache.Client

    def __init__(self, memcache_client: memcache.Client) -> None:
        self.memcache_client = memcache_client

    def set(self, key: bytes, value: Any, time: Optional[int] = None) -> bool:
        return self.memcache_client.set(key, value, time or 0)

    def set_multi(
        self,
        mapping: Dict[bytes, Any],
        time: Optional[int] = None,
        namespace: Optional[str] = None,
    ) -> None:
        self.memcache_client.set_multi(mapping, time=(time or 0), namespace=namespace)

    def get(self, key: bytes) -> Optional[Any]:
        return self.memcache_client.get(key)

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
