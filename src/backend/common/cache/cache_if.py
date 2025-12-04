from __future__ import annotations

import abc
from typing import Any, TypedDict

from backend.common.futures import TypedFuture

"""
A shim for the Legacy GAE memcache module

Primarily backed by Redis, but also with a noop implementation, for when caching is disabled

Implementats this API https://cloud.google.com/appengine/docs/standard/python/refdocs/google.appengine.api.memcache
"""


class CacheStats(TypedDict):
    hits: int
    misses: int


class CacheIf(abc.ABC):
    @abc.abstractmethod
    def set(self, key: bytes, value: Any, time: int | None = None) -> bool:
        """Sets a key's value, regardless of previous contents in cache.

        Unlike add() and replace(), this method always sets (or
        overwrites) the value in memcache, regardless of previous
        contents.

        Args:
        key: Key to set.  See docs on Client for details.
        value: Value to set.  Any type.  If complex, will be pickled.
        time: Optional expiration time, a relative number of seconds
            from current time (up to 1 month).
            By default, items never expire, though items may be evicted due to
            memory pressure.

        Returns:
        True if set.  False on error.
        """

    @abc.abstractmethod
    def set_async(
        self, key: bytes, value: Any, time: int | None = None
    ) -> TypedFuture[bool]: ...

    @abc.abstractmethod
    def set_multi(
        self,
        mapping: dict[bytes, Any],
        time: int | None = None,
        namespace: str | None = None,
    ) -> None:
        """Set multiple keys' values at once, regardless of previous contents.

        Args:
        mapping: Dictionary of keys to values.
        time: Optional expiration time, a relative number of seconds
            from current time (up to 1 month).
            By default, items never expire, though items may be evicted due to
            memory pressure.
        namespace: Optional namespace

        Returns:
        A list of keys whose values were NOT set.  On total success,
        this list should be empty.
        """

    @abc.abstractmethod
    def get(self, key: bytes) -> Any | None:
        """Looks up a single key in memcache.

        If you have multiple items to load, though, it's much more efficient
        to use get_multi() instead, which loads them in one bulk operation,
        reducing the networking latency that'd otherwise be required to do
        many serialized get() operations.

        Args:
        key: The key in memcache to look up.  See docs on Client
            for details of format.

        Returns:
        The value of the key, if found in memcache, else None.
        """

    @abc.abstractmethod
    def get_async(self, key: bytes) -> TypedFuture[Any | None]: ...

    @abc.abstractmethod
    def get_multi(
        self,
        keys: list[bytes],
        namespace: str | None = None,
    ) -> dict[bytes, Any | None]:
        """Looks up multiple keys from memcache in one operation.

        This is the recommended way to do bulk loads.

        Args:
        keys: List of keys to look up.  Keys may be strings or
            tuples of (hash_value, string).  Google App Engine
            does the sharding and hashing automatically, though, so the hash
            value is ignored.  To memcache, keys are just series of bytes,
            and not in any particular encoding.
        namespace: Optional namespace

        Returns:
        A dictionary of the keys and values that were present in memcache.
        Even if the key_prefix was specified, that key_prefix won't be on
        the keys in the returned dictionary.
        """

    @abc.abstractmethod
    def delete(self, key: bytes) -> None:
        """Deletes a key from memcache.

        Args:
        key: Key to delete.  See docs on Client for detils.
        """

    @abc.abstractmethod
    def delete_multi(self, keys: list[bytes]) -> None:
        """Delete multiple keys at once.

        Args:
        keys: List of keys to delete.
        """

    @abc.abstractmethod
    def incr(self, key: bytes) -> int | None:
        """Atomically increments a key's value.

        Internally, the value is a unsigned 64-bit integer.  Memcache
        doesn't check 64-bit overflows.  The value, if too large, will
        wrap around.


        Args:
        key: Key to increment.

        Returns:
        The new integer value of the key
        """

    @abc.abstractmethod
    def decr(self, key: bytes) -> int | None:
        """Atomically decrements a key's value.

        Internally, the value is a unsigned 64-bit integer.  Memcache
        doesn't check 64-bit overflows.  The value, if too large, will
        wrap around.


        Args:
        key: Key to decrement.

        Returns:
        The new integer value of the key
        """

    @abc.abstractmethod
    def get_stats(self) -> CacheStats | None:
        """Gets memcache statistics for this application.

        All of these statistics may reset due to various transient conditions. They
        provide the best information available at the time of being called.

        Returns:
        Dictionary mapping statistic names to associated values. Statistics and
        their associated meanings:

            hits: Number of cache get requests resulting in a cache hit.
            misses: Number of cache get requests resulting in a cache miss.
            byte_hits: Sum of bytes transferred on get requests. Rolls over to
            zero on overflow.
            items: Number of key/value pairs in the cache.
            bytes: Total size of all items in the cache.
            oldest_item_age: How long in seconds since the oldest item in the
            cache was accessed. Effectively, this indicates how long a new
            item will survive in the cache without being accessed. This is
            _not_ the amount of time that has elapsed since the item was
            created.

        On error, returns None.
        """
