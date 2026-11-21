from backend.common.memcache import MemcacheClient


def test_get_is_cached_until_reset(memcache_stub) -> None:
    MemcacheClient.reset()
    client = MemcacheClient.get()
    assert MemcacheClient.get() is client

    MemcacheClient.reset()
    assert MemcacheClient._cache is None
    assert MemcacheClient.get() is not client
