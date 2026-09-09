from unittest.mock import MagicMock

import pytest
from flask import Flask

from backend.api.handlers.helpers.etag_helper import (
    etag_deps_persisted_cache,
    get_incoming_etags,
    get_request_path,
    is_etag_valid,
    normalize_etag,
    save_etag_dependencies,
)
from backend.common.memcache import MemcacheClient


@pytest.fixture
def app() -> Flask:
    return Flask(__name__)


def test_normalize_etag() -> None:
    assert normalize_etag(None) is None
    assert normalize_etag("") is None
    assert normalize_etag("   ") is None
    assert normalize_etag("simple_etag") == "simple_etag"
    assert normalize_etag('"quoted_etag"') == "quoted_etag"
    assert normalize_etag("'single_quoted'") == "single_quoted"
    assert normalize_etag('W/"weak_etag"') == "weak_etag"
    assert normalize_etag('w/"weak_lowercase"') == "weak_lowercase"
    assert normalize_etag('  W/"  spaced_etag  "  ') == "spaced_etag"


def test_get_incoming_etags(app: Flask) -> None:
    with app.test_request_context(
        "/api/v3/team/frc254",
        headers={"If-None-Match": 'W/"etag1", "etag2", etag3'},
    ):
        etags = get_incoming_etags()
        assert set(etags) == {"etag1", "etag2", "etag3"}


def test_get_incoming_etags_empty(app: Flask) -> None:
    with app.test_request_context("/api/v3/team/frc254"):
        assert get_incoming_etags() == []


def test_get_request_path(app: Flask) -> None:
    with app.test_request_context("/api/v3/team/frc254?foo=bar"):
        assert get_request_path() == "/api/v3/team/frc254"
        assert (
            get_request_path("/api/v3/event/2020casj?year=2020")
            == "/api/v3/event/2020casj"
        )


def test_save_etag_dependencies_deduplicates(
    memcache_stub, monkeypatch: pytest.MonkeyPatch
) -> None:
    memcache = MemcacheClient.get()
    set_multi_mock = MagicMock(wraps=memcache.set_multi)
    monkeypatch.setattr(memcache, "set_multi", set_multi_mock)

    query_versions = {"team_k1": "ver1", "team_k2": "ver2"}

    # 1. First save: persists to Memcache and records in in-memory cache
    result1 = save_etag_dependencies(
        "etag_abc", query_versions, path="/api/v3/team/frc254"
    )
    assert result1 is True
    set_multi_mock.assert_called_once()
    assert etag_deps_persisted_cache.get(("/api/v3/team/frc254", "etag_abc")) is True

    # 2. Second save with identical (path, etag): skipped without Memcache calls
    set_multi_mock.reset_mock()
    result2 = save_etag_dependencies(
        "etag_abc", query_versions, path="/api/v3/team/frc254"
    )
    assert result2 is False
    set_multi_mock.assert_not_called()

    # 3. Save with altered ETag: persists to Memcache
    result3 = save_etag_dependencies(
        "etag_def", query_versions, path="/api/v3/team/frc254"
    )
    assert result3 is True
    set_multi_mock.assert_called_once()

    # 4. Save with different path but same ETag: persists independently
    set_multi_mock.reset_mock()
    result4 = save_etag_dependencies(
        "etag_abc", query_versions, path="/api/v3/team/frc9999"
    )
    assert result4 is True
    set_multi_mock.assert_called_once()


def test_save_etag_dependencies_empty_keys(memcache_stub) -> None:
    assert save_etag_dependencies("etag_empty", {}, path="/api/v3/team/frc254") is False
    assert etag_deps_persisted_cache.get(("/api/v3/team/frc254", "etag_empty")) is None


def test_save_etag_dependencies_cache_expiration(
    memcache_stub, monkeypatch: pytest.MonkeyPatch
) -> None:
    memcache = MemcacheClient.get()
    set_multi_mock = MagicMock(wraps=memcache.set_multi)
    monkeypatch.setattr(memcache, "set_multi", set_multi_mock)

    query_versions = {"team_k1": "ver1"}
    save_etag_dependencies("etag_expire", query_versions, path="/api/v3/team/frc254")
    set_multi_mock.assert_called_once()

    # Expire the in-memory cache entry
    etag_deps_persisted_cache.set(
        ("/api/v3/team/frc254", "etag_expire"), True, ttl_seconds=-1.0
    )
    assert etag_deps_persisted_cache.get(("/api/v3/team/frc254", "etag_expire")) is None

    # Calling save again must re-persist to Memcache
    set_multi_mock.reset_mock()
    result = save_etag_dependencies(
        "etag_expire", query_versions, path="/api/v3/team/frc254"
    )
    assert result is True
    set_multi_mock.assert_called_once()


def test_save_etag_dependencies_memcache_error_does_not_cache(
    memcache_stub, monkeypatch: pytest.MonkeyPatch
) -> None:
    memcache = MemcacheClient.get()
    monkeypatch.setattr(
        memcache,
        "set_multi",
        MagicMock(side_effect=Exception("Memcache write failed")),
    )

    result = save_etag_dependencies(
        "etag_err", {"k1": "ver1"}, path="/api/v3/team/frc254"
    )
    assert result is False
    # Must NOT be marked as persisted in memory after failure
    assert etag_deps_persisted_cache.get(("/api/v3/team/frc254", "etag_err")) is None


def test_is_etag_valid(memcache_stub) -> None:
    query_versions = {"q_k1": "ver1", "q_k2": "ver2"}
    save_etag_dependencies("etag_val", query_versions, path="/api/v3/team/frc254")

    # Valid ETag for matching path
    assert is_etag_valid("etag_val", path="/api/v3/team/frc254") is True

    # Invalid for different path
    assert is_etag_valid("etag_val", path="/api/v3/team/frc9999") is False

    # Invalid when unknown ETag
    assert is_etag_valid("unknown_etag", path="/api/v3/team/frc254") is False

    # Invalidate one query key in Memcache
    memcache = MemcacheClient.get()
    memcache.delete(b"q_ver:q_k1")
    assert is_etag_valid("etag_val", path="/api/v3/team/frc254") is False


def test_is_etag_valid_failure_evicts_from_persisted_cache(memcache_stub) -> None:
    query_versions = {"q_k1": "ver1"}
    save_etag_dependencies("etag_heal", query_versions, path="/api/v3/team/frc254")
    assert etag_deps_persisted_cache.get(("/api/v3/team/frc254", "etag_heal")) is True

    # Invalidate query key in Memcache
    memcache = MemcacheClient.get()
    memcache.delete(b"q_ver:q_k1")

    # is_etag_valid returns False and evicts from etag_deps_persisted_cache
    assert is_etag_valid("etag_heal", path="/api/v3/team/frc254") is False
    assert etag_deps_persisted_cache.get(("/api/v3/team/frc254", "etag_heal")) is None

    # Next save call will re-persist since it was evicted
    assert (
        save_etag_dependencies("etag_heal", query_versions, path="/api/v3/team/frc254")
        is True
    )
