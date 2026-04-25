from typing import Any, Generator, List

from google.appengine.ext import ndb
from werkzeug.test import Client

from backend.common.helpers.deferred import run_from_task
from backend.common.models.cached_query_result import CachedQueryResult
from backend.common.queries.database_query import CachedDatabaseQuery

# ---------------------------------------------------------------------------
# Minimal concrete CachedDatabaseQuery subclass used only in these tests
# ---------------------------------------------------------------------------


class _TestCachedQuery(CachedDatabaseQuery[List[ndb.Model], None]):
    CACHE_KEY_FORMAT = "test_admin_cache_{key}"
    CACHE_VERSION = 1
    DICT_CONVERTER = None
    CACHE_WRITES_ENABLED = False  # we build keys manually

    @ndb.tasklet
    def _query_async(self, key: str) -> Generator[Any, Any, List[ndb.Model]]:  # type: ignore[override]
        future = ndb.Future()
        future.set_result([])
        models = yield future
        return models


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_cache_key(partial: str, cache_version: int, db_version: int) -> str:
    """Build a cache key string identical to CachedDatabaseQuery.cache_key."""
    return f"{partial}:{cache_version}:{db_version}"


def _make_dict_cache_key(
    partial: str, cache_version: int, db_version: int, api_version: int
) -> str:
    """Build a dict-cache key (has a ~dictv suffix)."""
    base = _make_cache_key(partial, cache_version, db_version)
    return f"{base}~dictv{api_version}.0"


# ---------------------------------------------------------------------------
# /admin/cache  (GET)
# ---------------------------------------------------------------------------


def test_cache_list_empty(web_client: Client, login_gae_admin, ndb_stub) -> None:
    resp = web_client.get("/admin/cache")
    assert resp.status_code == 200
    assert b"Cached Database Queries" in resp.data
    assert b"Query Classes" in resp.data


def test_cache_list_does_not_render_global_version_stats(
    web_client: Client, login_gae_admin, ndb_stub
) -> None:
    CachedQueryResult(id=_make_cache_key("test_admin_cache_a", 1, 1), result=None).put()

    resp = web_client.get("/admin/cache")
    assert resp.status_code == 200

    body = resp.data.decode()
    # Should not show expensive global stats
    assert "Global DATABASE_QUERY_VERSION Stats" not in body
    # Should show version management section
    assert "Global Version Management" in body
    # Should have purge buttons for clearable versions
    assert "/admin/cache/purge_global/" in body


def test_cache_list_version_management_shows_correct_labels(
    web_client: Client, login_gae_admin, ndb_stub
) -> None:
    resp = web_client.get("/admin/cache")
    assert resp.status_code == 200

    body = resp.data.decode()
    # Should show current version as "Current"
    assert "Current" in body
    # Should show prior version as "Prior (Buffer)"
    assert "Prior (Buffer)" in body
    # Should show clearable versions as "Clearable"
    assert "Clearable" in body


def test_cache_list_renders_with_cached_entries(
    web_client: Client, login_gae_admin, ndb_stub
) -> None:
    CachedQueryResult(id=_make_cache_key("test_admin_cache_a", 1, 1), result=None).put()
    CachedQueryResult(
        id=_make_dict_cache_key("test_admin_cache_a", 1, 1, 3), result=None
    ).put()

    resp = web_client.get("/admin/cache")
    assert resp.status_code == 200
    assert b"Query Classes" in resp.data


# ---------------------------------------------------------------------------
# /admin/cache/purge_global/<db_version>  (POST)
# ---------------------------------------------------------------------------


def test_purge_global_version_redirects(
    web_client: Client, login_gae_admin, ndb_stub, taskqueue_stub
) -> None:
    current_v = CachedDatabaseQuery.DATABASE_QUERY_VERSION
    old_v = current_v - 2  # Must be < current_v - 1 to pass validation

    CachedQueryResult(
        id=_make_cache_key("test_admin_cache_x", 1, old_v), result=None
    ).put()

    resp = web_client.post(f"/admin/cache/purge_global/{old_v}")
    assert resp.status_code == 302
    assert "/admin/cache" in resp.headers["Location"]

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="cache-clearing")
    assert len(tasks) == len(CachedDatabaseQuery.__subclasses__())


def test_purge_global_version_deletes_old_only(
    web_client: Client, login_gae_admin, ndb_stub, taskqueue_stub
) -> None:
    current_v = CachedDatabaseQuery.DATABASE_QUERY_VERSION
    old_v = current_v - 2  # Must be < current_v - 1 to pass validation

    old_key1 = _make_cache_key("test_admin_cache_a", 1, old_v)
    old_key2 = _make_cache_key("test_admin_cache_b", 2, old_v)
    old_dict_key = _make_dict_cache_key("test_admin_cache_a", 1, old_v, 3)
    current_key = _make_cache_key("test_admin_cache_c", 1, current_v)

    CachedQueryResult(id=old_key1, result=None).put()
    CachedQueryResult(id=old_key2, result=None).put()
    CachedQueryResult(id=old_dict_key, result=None).put()
    CachedQueryResult(id=current_key, result=None).put()

    resp = web_client.post(f"/admin/cache/purge_global/{old_v}")
    assert resp.status_code == 302

    # Global purge now enqueues deferred tasks; nothing is deleted until they run
    assert CachedQueryResult.get_by_id(old_key1) is not None
    assert CachedQueryResult.get_by_id(old_key2) is not None
    assert CachedQueryResult.get_by_id(old_dict_key) is not None

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="cache-clearing")
    assert len(tasks) >= 1
    for task in tasks:
        run_from_task(task)

    # Old-version entries should be gone
    assert CachedQueryResult.get_by_id(old_key1) is None
    assert CachedQueryResult.get_by_id(old_key2) is None
    assert CachedQueryResult.get_by_id(old_dict_key) is None

    # Current-version entry must survive
    assert CachedQueryResult.get_by_id(current_key) is not None


def test_purge_global_version_noop_when_no_entries(
    web_client: Client, login_gae_admin, ndb_stub, taskqueue_stub
) -> None:
    """Purging a version that has no entries should not raise and should redirect."""
    # Use an old but positive version that simply has no data stored
    old_v = max(1, CachedDatabaseQuery.DATABASE_QUERY_VERSION - 2)

    resp = web_client.post(f"/admin/cache/purge_global/{old_v}")
    assert resp.status_code == 302

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="cache-clearing")
    assert len(tasks) == len(CachedDatabaseQuery.__subclasses__())


def test_cached_query_detail_normalizes_dict_db_version(
    web_client: Client, login_gae_admin, ndb_stub
) -> None:
    current_v = CachedDatabaseQuery.DATABASE_QUERY_VERSION
    old_v = current_v - 1

    CachedQueryResult(
        id=_make_cache_key("test_admin_cache_alpha", 1, old_v), result=None
    ).put()
    CachedQueryResult(
        id=_make_dict_cache_key("test_admin_cache_alpha", 1, old_v, 3), result=None
    ).put()

    resp = web_client.get("/admin/cache/_TestCachedQuery")
    assert resp.status_code == 200

    body = resp.data.decode()
    assert f"{old_v}~dictv" not in body


def test_cached_query_detail_breakdown_by_version_hides_protected_purge_links(
    web_client: Client, login_gae_admin, ndb_stub
) -> None:
    current_v = CachedDatabaseQuery.DATABASE_QUERY_VERSION
    clearable_v = current_v - 2

    clearable_key = _make_cache_key("test_admin_cache_clearable", 1, clearable_v)
    protected_key = _make_cache_key("test_admin_cache_protected", 1, current_v)

    CachedQueryResult(id=clearable_key, result=None).put()
    CachedQueryResult(id=protected_key, result=None).put()

    resp = web_client.get("/admin/cache/_TestCachedQuery")
    assert resp.status_code == 200

    body = resp.data.decode()
    assert f"/admin/cache/_TestCachedQuery/purge/{clearable_v}/1" in body
    assert f"/admin/cache/_TestCachedQuery/purge/{current_v}/1" not in body


def test_purge_version_deletes_dict_entries_for_version(
    web_client: Client, login_gae_admin, ndb_stub
) -> None:
    current_v = CachedDatabaseQuery.DATABASE_QUERY_VERSION
    old_v = current_v - 2  # Must be < current_v - 1 to pass validation

    plain_key = _make_cache_key("test_admin_cache_alpha", 2, old_v)
    dict_key = _make_dict_cache_key("test_admin_cache_alpha", 2, old_v, 3)
    other_version_key = _make_cache_key("test_admin_cache_alpha", 2, old_v + 1)

    CachedQueryResult(id=plain_key, result=None).put()
    CachedQueryResult(id=dict_key, result=None).put()
    CachedQueryResult(id=other_version_key, result=None).put()

    resp = web_client.post(f"/admin/cache/_TestCachedQuery/purge/{old_v}/2")
    assert resp.status_code == 302

    assert CachedQueryResult.get_by_id(plain_key) is None
    assert CachedQueryResult.get_by_id(dict_key) is None
    assert CachedQueryResult.get_by_id(other_version_key) is not None


def test_purge_version_rejects_protected_versions(
    web_client: Client, login_gae_admin, ndb_stub
) -> None:
    current_v = CachedDatabaseQuery.DATABASE_QUERY_VERSION

    # current version is protected
    resp = web_client.post(f"/admin/cache/_TestCachedQuery/purge/{current_v}/1")
    assert resp.status_code == 400

    # current - 1 (buffer) is also protected
    resp = web_client.post(f"/admin/cache/_TestCachedQuery/purge/{current_v - 1}/1")
    assert resp.status_code == 400

    # version 0 is invalid
    resp = web_client.post("/admin/cache/_TestCachedQuery/purge/0/1")
    assert resp.status_code == 400


def test_purge_version_not_accessible_without_login(
    web_client: Client, ndb_stub
) -> None:
    resp = web_client.post("/admin/cache/_TestCachedQuery/purge/1/1")
    assert resp.status_code == 401


def test_purge_global_version_not_accessible_without_login(
    web_client: Client, ndb_stub
) -> None:
    resp = web_client.post("/admin/cache/purge_global/1")
    assert resp.status_code == 401


def test_purge_class_global_version_redirects(
    web_client: Client, login_gae_admin, ndb_stub, taskqueue_stub
) -> None:
    current_v = CachedDatabaseQuery.DATABASE_QUERY_VERSION
    old_v = max(1, current_v - 2)  # Must be < current_v - 1 to pass validation

    CachedQueryResult(
        id=_make_cache_key("test_admin_cache_alpha", 1, old_v), result=None
    ).put()

    resp = web_client.post(f"/admin/cache/_TestCachedQuery/purge_global/{old_v}")
    assert resp.status_code == 302
    assert "/admin/cache/_TestCachedQuery" in resp.headers["Location"]


def test_purge_class_global_version_deletes_only_matching_class_and_version(
    web_client: Client, login_gae_admin, ndb_stub, taskqueue_stub
) -> None:
    current_v = CachedDatabaseQuery.DATABASE_QUERY_VERSION
    old_v = current_v - 2  # Must be < current_v - 1 to pass validation

    class_old_qv1 = _make_cache_key("test_admin_cache_alpha", 1, old_v)
    class_old_qv2 = _make_cache_key("test_admin_cache_beta", 2, old_v)
    class_old_dict = _make_dict_cache_key("test_admin_cache_beta", 2, old_v, 3)

    class_current = _make_cache_key("test_admin_cache_gamma", 1, current_v)
    other_class_same_version = _make_cache_key("other_prefix_delta", 1, old_v)

    CachedQueryResult(id=class_old_qv1, result=None).put()
    CachedQueryResult(id=class_old_qv2, result=None).put()
    CachedQueryResult(id=class_old_dict, result=None).put()
    CachedQueryResult(id=class_current, result=None).put()
    CachedQueryResult(id=other_class_same_version, result=None).put()

    resp = web_client.post(f"/admin/cache/_TestCachedQuery/purge_global/{old_v}")
    assert resp.status_code == 302

    # Per-class purge is now deferred; nothing deleted until tasks run
    assert CachedQueryResult.get_by_id(class_old_qv1) is not None

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="cache-clearing")
    assert len(tasks) == 1
    for task in tasks:
        run_from_task(task)

    assert CachedQueryResult.get_by_id(class_old_qv1) is None
    assert CachedQueryResult.get_by_id(class_old_qv2) is None
    assert CachedQueryResult.get_by_id(class_old_dict) is None

    assert CachedQueryResult.get_by_id(class_current) is not None
    assert CachedQueryResult.get_by_id(other_class_same_version) is not None


def test_purge_class_global_version_defers_task(
    web_client: Client, login_gae_admin, ndb_stub, taskqueue_stub
) -> None:
    """Per-class global purge should enqueue a task, not delete synchronously."""
    current_v = CachedDatabaseQuery.DATABASE_QUERY_VERSION
    old_v = current_v - 2

    old_key = _make_cache_key("test_admin_cache_alpha", 1, old_v)
    CachedQueryResult(id=old_key, result=None).put()

    resp = web_client.post(f"/admin/cache/_TestCachedQuery/purge_global/{old_v}")
    assert resp.status_code == 302

    # Must not have been deleted immediately — must be deferred
    assert CachedQueryResult.get_by_id(old_key) is not None
    tasks = taskqueue_stub.get_filtered_tasks(queue_names="cache-clearing")
    assert len(tasks) == 1


def test_purge_class_global_version_rejects_protected_versions(
    web_client: Client, login_gae_admin, ndb_stub
) -> None:
    current_v = CachedDatabaseQuery.DATABASE_QUERY_VERSION

    # current version is protected
    resp = web_client.post(f"/admin/cache/_TestCachedQuery/purge_global/{current_v}")
    assert resp.status_code == 400

    # current - 1 (buffer) is also protected
    resp = web_client.post(
        f"/admin/cache/_TestCachedQuery/purge_global/{current_v - 1}"
    )
    assert resp.status_code == 400


def test_purge_class_global_version_not_found(
    web_client: Client, login_gae_admin, ndb_stub
) -> None:
    resp = web_client.post("/admin/cache/NotARealQuery/purge_global/1")
    assert resp.status_code == 404


def test_purge_class_global_version_not_accessible_without_login(
    web_client: Client, ndb_stub
) -> None:
    resp = web_client.post("/admin/cache/_TestCachedQuery/purge_global/1")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# CachedDatabaseQuery class methods
# ---------------------------------------------------------------------------


def test_get_query_class_by_name_found() -> None:
    """Test finding a query class by name."""
    query_class = CachedDatabaseQuery.get_query_class_by_name("_TestCachedQuery")
    assert query_class is not None
    assert query_class.__name__ == "_TestCachedQuery"
    assert query_class is _TestCachedQuery


def test_get_query_class_by_name_not_found() -> None:
    """Test that None is returned for non-existent class."""
    query_class = CachedDatabaseQuery.get_query_class_by_name("NotARealQueryClass")
    assert query_class is None


def test_validate_db_version_for_deletion_valid() -> None:
    """Test that old versions are accepted."""
    current_version = CachedDatabaseQuery.DATABASE_QUERY_VERSION
    # current - 2 should be safe to delete
    CachedDatabaseQuery.validate_db_version_for_deletion(current_version - 2)
    # current - 3 should also be safe
    CachedDatabaseQuery.validate_db_version_for_deletion(current_version - 3)


def test_validate_db_version_for_deletion_rejects_positive_rules() -> None:
    """Test that versions must be positive."""
    import pytest

    with pytest.raises(ValueError, match="must be a positive integer"):
        CachedDatabaseQuery.validate_db_version_for_deletion(0)

    with pytest.raises(ValueError, match="must be a positive integer"):
        CachedDatabaseQuery.validate_db_version_for_deletion(-1)


def test_validate_db_version_for_deletion_rejects_recent() -> None:
    """Test that recent versions (current and current-1) are rejected."""
    import pytest

    current_version = CachedDatabaseQuery.DATABASE_QUERY_VERSION
    min_safe = current_version - 1

    with pytest.raises(ValueError, match=f"must be less than {min_safe}"):
        CachedDatabaseQuery.validate_db_version_for_deletion(current_version)

    with pytest.raises(ValueError, match=f"must be less than {min_safe}"):
        CachedDatabaseQuery.validate_db_version_for_deletion(min_safe)
