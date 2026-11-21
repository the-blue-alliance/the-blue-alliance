from backend.common.cache.noop_cache import NoopCache


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


def test_noop_cache_async() -> None:
    cache = NoopCache()

    assert cache.set_async(b"key", "value").get_result() is True
    assert cache.get_async(b"key").get_result() is None
    assert cache.miss_count == 1
