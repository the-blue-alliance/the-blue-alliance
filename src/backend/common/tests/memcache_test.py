import datetime
from unittest.mock import Mock

import fakeredis
import pytest
import redis
from _pytest.monkeypatch import MonkeyPatch
from freezegun import freeze_time

from backend.common import memcache as memcache_module
from backend.common.memcache import CacheIf, MemcacheClient, NoopCache, RedisCache
from backend.common.redis import RedisClient


@pytest.fixture
def redis_client() -> redis.Redis:
    return fakeredis.FakeStrictRedis()


@pytest.fixture
def redis_cache(redis_client: redis.Redis) -> CacheIf:
    return RedisCache(redis_client)


@pytest.fixture(autouse=True)
def clear_state() -> None:
    RedisClient.reset()
    MemcacheClient.reset()


def test_noop_cache() -> None:
    cache = NoopCache()

    assert cache.get(b"key") is None
    assert cache.set(b"key", "value") is True
    assert cache.get(b"key") is None

    stats = cache.get_stats()
    assert stats is not None
    assert stats["misses"] == 2

    assert cache.get_multi([b"key"]) == {b"key": None}
    assert cache.set_multi({b"key": "value"}) is None
    assert cache.get_multi([b"key"]) == {b"key": None}

    assert cache.delete(b"key") is None
    assert cache.delete_multi([b"key"]) is None

    assert cache.incr(b"key") is None
    assert cache.decr(b"key") is None

    stats = cache.get_stats()
    assert stats is not None
    assert stats["misses"] == 4


def test_single_key_get_set_delete(redis_cache: CacheIf) -> None:
    assert redis_cache.get(b"key") is None
    assert redis_cache.set(b"key", "value") is True
    assert redis_cache.get(b"key") == "value"
    redis_cache.delete(b"key")
    assert redis_cache.get(b"key") is None


def test_multi_key_get_set_delete(redis_cache: CacheIf) -> None:
    assert redis_cache.get_multi([b"key1", b"key2"]) == {b"key1": None, b"key2": None}
    redis_cache.set_multi({b"key1": "value1", b"key2": "value2"})
    assert redis_cache.get_multi([b"key1", b"key2"]) == {
        b"key1": "value1",
        b"key2": "value2",
    }
    redis_cache.delete_multi([b"key1", b"key2"])
    assert redis_cache.get_multi([b"key1", b"key2"]) == {b"key1": None, b"key2": None}


def test_redis_ttl(redis_cache: CacheIf) -> None:
    start_time = datetime.datetime.now()
    with freeze_time(start_time) as frozen_time:
        redis_cache.set(b"key", "value", time=10)
        assert redis_cache.get(b"key") == "value"

        frozen_time.move_to(start_time + datetime.timedelta(seconds=40))
        assert redis_cache.get(b"key") is None


def test_redis_multi_set_ttl(redis_cache: CacheIf) -> None:
    start_time = datetime.datetime.now()
    with freeze_time(start_time) as frozen_time:
        redis_cache.set_multi({b"key1": "value1", b"key2": "value2"}, time=10)
        assert redis_cache.get(b"key1") == "value1"
        assert redis_cache.get(b"key2") == "value2"

        frozen_time.move_to(start_time + datetime.timedelta(seconds=40))
        assert redis_cache.get(b"key1") is None
        assert redis_cache.get(b"key2") is None


def test_read_old_version(redis_cache: CacheIf) -> None:
    redis_cache.set(b"key1", "value1")
    memcache_module.REDIS_CACHE_ITEM_VERSION += 1
    redis_cache.set(b"key2", "value2")

    assert redis_cache.get(b"key1") is None
    assert redis_cache.get(b"key2") == "value2"
    assert redis_cache.get_multi([b"key1", b"key2"]) == {
        b"key1": None,
        b"key2": "value2",
    }


def test_redis_encode_round_trip(redis_cache: CacheIf) -> None:
    values = [1, "a", b"asdf", 3.14, 1337, True, False, ["a", "b", 3], {"abc": 123}]
    for i, value in enumerate(values):
        key = f"key_{i}".encode()
        assert redis_cache.set(key, value) is True
        assert redis_cache.get(key) == value


def test_incr_decr(redis_cache: CacheIf) -> None:
    key = b"key"
    assert redis_cache.get(key) is None
    assert redis_cache.incr(key) == 1
    assert redis_cache.incr(key) == 2
    assert redis_cache.incr(key) == 3
    assert redis_cache.decr(key) == 2
    assert redis_cache.decr(key) == 1


def test_memcache_client_no_env() -> None:
    client = MemcacheClient.get()
    assert isinstance(client, NoopCache)


def test_memcache_client_empty_env(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("REDIS_CACHE_URL", "")
    client = MemcacheClient.get()
    assert isinstance(client, NoopCache)


def test_memcache_client_with_env(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("REDIS_CACHE_URL", "redis://localhost:1234")

    def from_url_patch(url):
        return Mock()

    monkeypatch.setattr(redis.Redis, "from_url", from_url_patch)

    client = MemcacheClient.get()
    assert isinstance(client, RedisCache)
