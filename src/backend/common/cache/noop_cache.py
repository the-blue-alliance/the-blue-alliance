from typing import Any, Dict, List, Optional

from backend.common.cache.cache_if import CacheIf, CacheStats


class NoopCache(CacheIf):
    """
    A noop implementation of the memcache interface, where all writes succeed and all reads miss
    """

    miss_count: int

    def __init__(self) -> None:
        self.miss_count = 0

    def set(self, key: bytes, value: Any, time: Optional[int] = None) -> bool:
        return True

    def set_multi(
        self,
        mapping: Dict[bytes, Any],
        time: Optional[int] = None,
    ) -> None:
        return None

    def get(self, key: bytes) -> Optional[Any]:
        self.miss_count += 1
        return None

    def get_multi(
        self,
        keys: List[bytes],
    ) -> Dict[bytes, Optional[Any]]:
        self.miss_count += len(keys)
        return {k: None for k in keys}

    def delete(self, key: bytes) -> None:
        return None

    def delete_multi(self, keys: List[bytes]) -> None:
        return None

    def incr(self, key: bytes) -> Optional[int]:
        return None

    def decr(self, key: bytes) -> Optional[int]:
        return None

    def get_stats(self) -> Optional[CacheStats]:
        return CacheStats(
            hits=0,
            misses=self.miss_count,
        )
