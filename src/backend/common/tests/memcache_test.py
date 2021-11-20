from unittest.mock import Mock

import pytest
import redis
from _pytest.monkeypatch import MonkeyPatch

from backend.common.memcache import MemcacheClient, NoopCache, RedisCache


@pytest.fixture(autouse=True)
def clear_state() -> None:
    MemcacheClient.reset()


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
