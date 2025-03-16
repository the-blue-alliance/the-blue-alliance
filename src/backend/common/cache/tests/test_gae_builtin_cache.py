import pytest
from google.appengine.api import memcache

from backend.common.cache.gae_builtin_cache import AppEngineBuiltinCache


@pytest.fixture
def mc(memcache_stub) -> memcache.Client:
    return memcache.Client()


@pytest.fixture
def cache(mc: memcache.Client) -> AppEngineBuiltinCache:
    return AppEngineBuiltinCache(mc)


def test_set(mc: memcache.Client, cache: AppEngineBuiltinCache) -> None:
    assert cache.set(b"foo", "bar") is True
    assert mc.get(b"foo") == "bar"


def test_set_async(mc: memcache.Client, cache: AppEngineBuiltinCache) -> None:
    assert cache.set_async(b"foo", "bar").get_result() is True
    assert mc.get(b"foo") == "bar"


def test_set_multi(mc: memcache.Client, cache: AppEngineBuiltinCache) -> None:
    cache.set_multi({b"foo": "bar", b"woof": "meow"})
    assert mc.get_multi([b"foo", b"woof"]) == {b"foo": "bar", b"woof": "meow"}


def test_get(mc: memcache.Client, cache: AppEngineBuiltinCache) -> None:
    mc.set(b"foo", "bar")
    assert cache.get(b"foo") == "bar"


def test_get_async(mc: memcache.Client, cache: AppEngineBuiltinCache) -> None:
    mc.set(b"foo", "bar")
    assert cache.get_async(b"foo").get_result() == "bar"


def test_get_multi(mc: memcache.Client, cache: AppEngineBuiltinCache) -> None:
    mc.set_multi({b"foo": "bar", b"woof": "meow"})
    assert cache.get_multi([b"foo", b"woof"]) == {b"foo": "bar", b"woof": "meow"}


def test_delete(mc: memcache.Client, cache: AppEngineBuiltinCache) -> None:
    mc.set(b"foo", "bar")
    cache.delete(b"foo")
    assert mc.get(b"foo") is None


def test_delete_multi(mc: memcache.Client, cache: AppEngineBuiltinCache):
    mc.set_multi({b"foo": "bar", b"woof": "meow"})
    cache.delete_multi([b"foo", b"woof"])
    assert mc.get_multi([b"foo", b"woof"]) == {}


def test_incr(mc: memcache.Client, cache: AppEngineBuiltinCache) -> None:
    mc.set(b"foo", 0)
    cache.incr(b"foo")
    assert mc.get(b"foo") == 1


def test_decr(mc: memcache.Client, cache: AppEngineBuiltinCache) -> None:
    mc.set(b"foo", 5)
    cache.decr(b"foo")
    assert mc.get(b"foo") == 4


def test_get_stats(mc: memcache.Client, cache: AppEngineBuiltinCache) -> None:
    assert mc.get_stats() == cache.get_stats()
