import pickle
import zlib
from unittest.mock import Mock

import pytest

from backend.common.cache.flask_response_cache import MemcacheFlaskResponseCache


@pytest.fixture
def client() -> Mock:
    return Mock()


@pytest.fixture
def cache(client: Mock) -> MemcacheFlaskResponseCache:
    return MemcacheFlaskResponseCache(client)


def test_dump_load_round_trip(cache: MemcacheFlaskResponseCache) -> None:
    assert cache.dump_object(5) == b"5"
    assert cache.load_object(cache.dump_object(5)) == 5
    assert cache.load_object(cache.dump_object({"a": 1})) == {"a": 1}


def test_load_object_none(cache: MemcacheFlaskResponseCache) -> None:
    assert cache.load_object(None) is None  # pyre-ignore[6]


def test_load_object_unpicklable(cache: MemcacheFlaskResponseCache) -> None:
    # A truncated pickle stream raises UnpicklingError, a PickleError subclass
    bad = b"!" + zlib.compress(pickle.dumps({"a": 1})[:-1])
    assert cache.load_object(bad) is None


def test_load_object_raw_bytes(cache: MemcacheFlaskResponseCache) -> None:
    assert cache.load_object(b"not-an-int") == b"not-an-int"


def test_get_and_get_dict(cache: MemcacheFlaskResponseCache, client: Mock) -> None:
    client.get.return_value = b"7"
    assert cache.get("k") == 7

    client.get_multi.return_value = {"a": b"1", "b": cache.dump_object("x")}
    assert cache.get_dict("a", "b") == {"a": 1, "b": "x"}
    assert cache.get_many("a", "b", "c") == [1, "x", None]


def test_writes(cache: MemcacheFlaskResponseCache, client: Mock) -> None:
    client.set.return_value = True
    assert cache.set("k", 1) is True
    client.set.assert_called_once_with("k", b"1", 0)

    client.add.return_value = True
    assert cache.add("k", 2, timeout=10) is True
    client.add.assert_called_once_with("k", b"2", 10)

    client.set_multi.return_value = []
    assert cache.set_many({"a": 1}) is True
    client.set_multi.return_value = ["a"]
    assert cache.set_many({"a": 1}) is False


def test_deletes_and_counters(cache: MemcacheFlaskResponseCache, client: Mock) -> None:
    client.delete.return_value = True
    assert cache.delete("k") is True

    client.delete_multi.return_value = True
    assert cache.delete_many("a", "b") is True
    client.delete_multi.assert_called_once_with(("a", "b"))

    client.flush_all.return_value = True
    assert cache.clear() is True

    client.incr.return_value = 3
    assert cache.inc("k", 2) == 3
    client.incr.assert_called_once_with("k", 2)

    client.decr.return_value = 1
    assert cache.dec("k") == 1
    client.decr.assert_called_once_with("k", 1)


def test_has_not_implemented(cache: MemcacheFlaskResponseCache) -> None:
    with pytest.raises(NotImplementedError):
        cache.has("k")
