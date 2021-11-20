import datetime

import fakeredis
import pytest
import redis
from freezegun import freeze_time

import backend.common.cache.redis_cache as redis_cache_module
from backend.common.cache.cache_if import CacheIf
from backend.common.cache.redis_cache import RedisCache
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
    redis_cache_module.REDIS_CACHE_ITEM_VERSION += 1
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
