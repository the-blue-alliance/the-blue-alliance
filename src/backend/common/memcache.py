from __future__ import annotations

import abc
import enum
import pickle
import struct
from dataclasses import dataclass, field as dataclass_field
from typing import Any, Dict, List, Optional, TypedDict

import redis
from pyre_extensions import none_throws

from backend.common.redis import RedisClient


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
    def set(self, key: bytes, value: Any, time: Optional[int] = None) -> bool:
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
    def set_multi(
        self,
        mapping: Dict[bytes, Any],
        time: Optional[int] = None,
    ) -> None:
        """Set multiple keys' values at once, regardless of previous contents.

        Args:
        mapping: Dictionary of keys to values.
        time: Optional expiration time, a relative number of seconds
            from current time (up to 1 month).
            By default, items never expire, though items may be evicted due to
            memory pressure.

        Returns:
        A list of keys whose values were NOT set.  On total success,
        this list should be empty.
        """

    @abc.abstractmethod
    def get(self, key: bytes) -> Optional[Any]:
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
    def get_multi(
        self,
        keys: List[bytes],
    ) -> Dict[bytes, Optional[Any]]:
        """Looks up multiple keys from memcache in one operation.

        This is the recommended way to do bulk loads.

        Args:
        keys: List of keys to look up.  Keys may be strings or
            tuples of (hash_value, string).  Google App Engine
            does the sharding and hashing automatically, though, so the hash
            value is ignored.  To memcache, keys are just series of bytes,
            and not in any particular encoding.

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
    def delete_multi(self, keys: List[bytes]) -> None:
        """Delete multiple keys at once.

        Args:
        keys: List of keys to delete.
        """

    @abc.abstractmethod
    def incr(self, key: bytes) -> Optional[int]:
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
    def decr(self, key: bytes) -> Optional[int]:
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
    def get_stats(self) -> Optional[CacheStats]:
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


REDIS_CACHE_ITEM_VERSION = 0


class _RedisCacheValueType(enum.IntEnum):
    BYTES = 0
    UNICODE = 1
    PICKLED = 2
    INT = 3
    BOOL = 4


@dataclass
class _RedisCacheItem:
    value_type: _RedisCacheValueType
    value: Any
    version: int

    # This will pack the data type + version into unsigned chars
    # (one byte, so 0-255 values)
    HEADER_PACK_FMT: str = dataclass_field(
        default="<BB", init=False, repr=False, compare=False, hash=None
    )
    HEADER_LEN: int = dataclass_field(
        default=2, init=False, repr=False, compare=False, hash=None
    )

    def __bytes__(self) -> bytes:
        # First, pack a brief header that includes the version and data type
        header = struct.pack(self.HEADER_PACK_FMT, self.version, int(self.value_type))

        value_bytes: Optional[bytes] = None
        if self.value_type == _RedisCacheValueType.BYTES:
            value_bytes = self.value
        elif self.value_type == _RedisCacheValueType.UNICODE:
            value_bytes = self.value.encode("utf-8")
        elif self.value_type == _RedisCacheValueType.PICKLED:
            value_bytes = pickle.dumps(self.value, protocol=pickle.HIGHEST_PROTOCOL)
        elif self.value_type == _RedisCacheValueType.INT:
            value_bytes = bytes(
                self.value.to_bytes(
                    (self.value.bit_length() + 7) // 8,
                    byteorder="little",
                    signed=True,
                )
            )
        elif self.value_type == _RedisCacheValueType.BOOL:
            value_bytes = bytes(
                int(self.value).to_bytes(1, byteorder="little", signed=False)
            )
        else:
            raise ValueError(f"Can't turn value type {self.value_type} into bytes!")
        return header + none_throws(value_bytes)

    @classmethod
    def from_bytes(cls, raw_data: bytes) -> _RedisCacheItem:
        header = struct.unpack(cls.HEADER_PACK_FMT, raw_data[: cls.HEADER_LEN])
        version = header[0]
        value_type = _RedisCacheValueType(header[1])
        value_data = raw_data[cls.HEADER_LEN :]

        value = None
        if value_type == _RedisCacheValueType.BYTES:
            value = value_data
        elif value_type == _RedisCacheValueType.UNICODE:
            value = value_data.decode("utf-8")
        elif value_type == _RedisCacheValueType.PICKLED:
            value = pickle.loads(value_data)
        elif value_type == _RedisCacheValueType.INT:
            value = int.from_bytes(value_data, byteorder="little", signed=True)
        elif value_type == _RedisCacheValueType.BOOL:
            value = bool(int.from_bytes(value_data, byteorder="little", signed=False))
        else:
            raise ValueError(f"Unable to get value of type {value_type}")

        return cls(
            version=version,
            value_type=value_type,
            value=none_throws(value),
        )

    @classmethod
    def from_value(cls, value: Any) -> _RedisCacheItem:
        value_type: Optional[_RedisCacheValueType] = None

        if isinstance(value, bytes):
            value_type = _RedisCacheValueType.BYTES
        elif isinstance(value, str):
            value_type = _RedisCacheValueType.UNICODE
        elif isinstance(value, bool):
            value_type = _RedisCacheValueType.BOOL
        elif isinstance(value, int):
            value_type = _RedisCacheValueType.INT
        else:
            value_type = _RedisCacheValueType.PICKLED

        return cls(
            version=REDIS_CACHE_ITEM_VERSION,
            value_type=none_throws(value_type),
            value=value,
        )


class RedisCache(CacheIf):
    """
    A cache implementation backed by redis

    The GAE memcache service will transparently (de)pickle objects that get stored,
    so we do the same here, but a bit simpler (where we bindly pickle everything, instead
    of checking the value's type)
    """

    redis_client: redis.Redis

    def __init__(self, redis_client: redis.Redis) -> None:
        self.redis_client = redis_client

    def set(self, key: bytes, value: Any, time: Optional[int] = None) -> bool:
        if time is not None and time < 0:
            raise ValueError("Expiration must not be negative")

        encoded_value = bytes(_RedisCacheItem.from_value(value))
        ret = self.redis_client.set(key, encoded_value, ex=time)
        if ret is None:
            return False
        return ret

    def set_multi(
        self,
        mapping: Dict[bytes, Any],
        time: Optional[int] = None,
    ) -> None:
        if time is not None and time < 0:
            raise ValueError("Expiration must not be negative")

        mapping_to_set = {
            k: bytes(_RedisCacheItem.from_value(v)) for k, v in mapping.items()
        }
        pipeline = self.redis_client.pipeline()
        pipeline.mset(mapping_to_set)
        if time is not None:
            # Redis doesn't support mset + TTL, so we do it
            # ourselves manually in a transaction, if necessary
            for k in mapping.keys():
                pipeline.expire(k, time)
        pipeline.execute()

    def get(self, key: bytes) -> Optional[Any]:
        value = self.redis_client.get(key)
        if value is None:
            return None

        data = _RedisCacheItem.from_bytes(value)
        if data.version < REDIS_CACHE_ITEM_VERSION:
            return None
        return data.value

    def get_multi(
        self,
        keys: List[bytes],
    ) -> Dict[bytes, Optional[Any]]:
        values = self.redis_client.mget(keys)
        data_map = {
            k: _RedisCacheItem.from_bytes(v) if v is not None else None
            for k, v in zip(keys, values)
        }
        return {
            k: v.value
            if v is not None and v.version == REDIS_CACHE_ITEM_VERSION
            else None
            for k, v in data_map.items()
        }

    def delete(self, key: bytes) -> None:
        self.redis_client.delete(key)

    def delete_multi(self, keys: List[bytes]) -> None:
        self.redis_client.delete(*keys)

    def incr(self, key: bytes) -> Optional[int]:
        return self.redis_client.incr(key)

    def decr(self, key: bytes) -> Optional[int]:
        return self.redis_client.decr(key)

    def get_stats(self) -> Optional[CacheStats]:
        info = self.redis_client.info(section="stats")
        return CacheStats(
            hits=info["keyspace_hits"],
            misses=info["keyspace_misses"],
        )


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
