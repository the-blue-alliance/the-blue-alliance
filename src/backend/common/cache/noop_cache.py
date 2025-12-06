from typing import Any

from backend.common.cache.cache_if import CacheIf, CacheStats
from backend.common.futures import InstantFuture, TypedFuture


class NoopCache(CacheIf):
    """
    A noop implementation of the memcache interface, where all writes succeed and all reads miss
    """

    miss_count: int

    def __init__(self) -> None:
        self.miss_count = 0

    def set(self, key: bytes, value: Any, time: int | None = None) -> bool:
        return True

    def set_async(
        self, key: bytes, value: Any, time: int | None = None
    ) -> TypedFuture[bool]:
        return InstantFuture(True)  # pyre-ignore[7]

    def set_multi(
        self,
        mapping: dict[bytes, Any],
        time: int | None = None,
        namespace: str | None = None,
    ) -> None:
        return None

    def get(self, key: bytes) -> Any | None:
        self.miss_count += 1
        return None

    def get_async(self, key: bytes) -> TypedFuture[Any | None]:
        self.miss_count += 1
        return InstantFuture(None)

    def get_multi(
        self,
        keys: list[bytes],
        namespace: str | None = None,
    ) -> dict[bytes, Any | None]:
        self.miss_count += len(keys)
        return {k: None for k in keys}

    def delete(self, key: bytes) -> None:
        return None

    def delete_multi(self, keys: list[bytes]) -> None:
        return None

    def incr(self, key: bytes) -> int | None:
        return None

    def decr(self, key: bytes) -> int | None:
        return None

    def get_stats(self) -> CacheStats | None:
        return CacheStats(
            hits=0,
            misses=self.miss_count,
        )
