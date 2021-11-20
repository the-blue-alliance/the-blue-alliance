from __future__ import annotations

import enum
import pickle
import struct
from dataclasses import dataclass, field as dataclass_field
from typing import Any, Dict, List, Optional

import redis
from pyre_extensions import none_throws

from backend.common.cache.cache_if import CacheIf, CacheStats


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
        pipeline.mset(mapping_to_set)  # pyre-ignore[6]
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
