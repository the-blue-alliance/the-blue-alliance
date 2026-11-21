from __future__ import annotations

import time
from collections import OrderedDict
from dataclasses import dataclass
from threading import Lock
from typing import Generic, Optional, TypeVar

K = TypeVar("K")
V = TypeVar("V")


@dataclass(frozen=True)
class _CacheEntry(Generic[V]):
    value: V
    expires_at: float


class InstanceCache(Generic[K, V]):
    """
    A thread-safe, in-memory LRU cache with per-item TTL expiration.

    Design & Concurrency Guarantees:
    - Deadlock-free: The lock is held exclusively during internal dictionary
      read/write operations. No callbacks, external functions, I/O operations,
      or coroutine yields occur within the critical section.
    - O(1) LRU eviction via OrderedDict.
    - System clock skew resilient via time.monotonic().
    """

    def __init__(self, ttl_seconds: float = 3600.0, max_size: int = 1000) -> None:
        self._ttl_seconds: float = ttl_seconds
        self._max_size: int = max_size
        self._cache: OrderedDict[K, _CacheEntry[V]] = OrderedDict()
        self._lock: Lock = Lock()

    @property
    def ttl_seconds(self) -> float:
        return self._ttl_seconds

    @property
    def max_size(self) -> int:
        return self._max_size

    def get(self, key: K) -> Optional[V]:
        now = time.monotonic()
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None
            if entry.expires_at <= now:
                del self._cache[key]
                return None
            self._cache.move_to_end(key)
            return entry.value

    def set(self, key: K, value: V, ttl_seconds: Optional[float] = None) -> None:
        ttl = self._ttl_seconds if ttl_seconds is None else ttl_seconds
        expires_at = time.monotonic() + ttl
        entry = _CacheEntry(value=value, expires_at=expires_at)
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            self._cache[key] = entry
            while len(self._cache) > self._max_size:
                self._cache.popitem(last=False)

    def delete(self, key: K) -> bool:
        with self._lock:
            return self._cache.pop(key, None) is not None

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._cache)

    def __contains__(self, key: K) -> bool:
        return self.get(key) is not None
