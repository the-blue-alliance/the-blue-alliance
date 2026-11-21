from typing import Any, Generator, List
from unittest.mock import patch

import pytest
from google.appengine.ext import ndb
from werkzeug.test import Client

from backend.common.consts.comp_level import CompLevel
from backend.common.consts.event_type import EventType
from backend.common.helpers.deferred import run_from_task
from backend.common.manipulators.event_details_manipulator import (
    EventDetailsManipulator,
)
from backend.common.manipulators.event_manipulator import EventManipulator
from backend.common.manipulators.match_manipulator import MatchManipulator
from backend.common.manipulators.team_manipulator import TeamManipulator
from backend.common.models.cached_query_result import CachedQueryResult
from backend.common.models.event import Event
from backend.common.models.event_details import EventDetails
from backend.common.models.match import Match
from backend.common.models.team import Team
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


def test_cache_list_offers_only_orphan_purge(
    web_client: Client, login_gae_admin, ndb_stub
) -> None:
    resp = web_client.get("/admin/cache")
    assert resp.status_code == 200

    body = resp.data.decode()
    assert 'action="/admin/cache/purge_orphans"' in body
    assert "purge_global" not in body
    assert "Global Version Management" not in body


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


# ---------------------------------------------------------------------------
# /admin/cache/<query_class_name>  (POST - cache key lookup)
# ---------------------------------------------------------------------------


def test_cached_query_key_lookup_missing_cache_key(
    web_client: Client, login_gae_admin, ndb_stub
) -> None:
    resp = web_client.post("/admin/cache/_TestCachedQuery", data={})
    assert resp.status_code == 400


def test_cached_query_key_lookup_full_key_redirects(
    web_client: Client, login_gae_admin, ndb_stub
) -> None:
    resp = web_client.post(
        "/admin/cache/_TestCachedQuery",
        data={"cache_key": "test_admin_cache_a:1:6"},
    )
    assert resp.status_code == 302
    assert (
        resp.headers["Location"]
        == "/admin/cache/_TestCachedQuery/test_admin_cache_a:1:6"
    )


def test_cached_query_key_lookup_partial_key_unknown_class(
    web_client: Client, login_gae_admin, ndb_stub
) -> None:
    resp = web_client.post(
        "/admin/cache/NotARealQuery",
        data={"cache_key": "test_admin_cache_a"},
    )
    assert resp.status_code == 404


def test_cached_query_key_lookup_partial_key_expands(
    web_client: Client, login_gae_admin, ndb_stub
) -> None:
    resp = web_client.post(
        "/admin/cache/_TestCachedQuery",
        data={"cache_key": "test_admin_cache_a"},
    )
    assert resp.status_code == 302
    expected_key = _make_cache_key(
        "test_admin_cache_a",
        _TestCachedQuery.CACHE_VERSION,
        CachedDatabaseQuery.DATABASE_QUERY_VERSION,
    )
    assert resp.headers["Location"] == f"/admin/cache/_TestCachedQuery/{expected_key}"


# ---------------------------------------------------------------------------
# /admin/cache/<query_class_name>  (GET)
# ---------------------------------------------------------------------------


def test_cached_query_detail_not_found(
    web_client: Client, login_gae_admin, ndb_stub
) -> None:
    resp = web_client.get("/admin/cache/NotARealQuery")
    assert resp.status_code == 404


def test_cached_query_detail_counts_by_version(
    web_client: Client, login_gae_admin, ndb_stub
) -> None:
    current_v = CachedDatabaseQuery.DATABASE_QUERY_VERSION
    CachedQueryResult(id=_make_cache_key("test_admin_cache_a", 1, current_v)).put()
    CachedQueryResult(id=_make_cache_key("test_admin_cache_b", 1, current_v)).put()
    CachedQueryResult(id=_make_cache_key("test_admin_cache_c", 2, current_v)).put()
    # Malformed keys (missing / non-numeric version parts) are counted in the
    # total but skipped in the per-version breakdown
    CachedQueryResult(id="test_admin_cache_d").put()
    CachedQueryResult(id="test_admin_cache_e:abc:def").put()

    resp = web_client.get("/admin/cache/_TestCachedQuery")
    assert resp.status_code == 200
    body = resp.data.decode()
    assert "_TestCachedQuery" in body
    assert f"/admin/cache/_TestCachedQuery/purge/{current_v}/1" not in body


def test_cached_query_detail_skips_keys_without_string_id(
    web_client: Client, login_gae_admin, ndb_stub, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Datastore keys in the prefix range always have string ids; simulate an
    # integer-id key to exercise the defensive branch.
    def fake_iter(cls, prefix: str, page_size: int):
        yield ndb.Key(CachedQueryResult, 12345)
        yield ndb.Key(CachedQueryResult, _make_cache_key("test_admin_cache_a", 1, 1))

    monkeypatch.setattr(
        CachedQueryResult,
        "iter_keys_by_cache_key_prefix",
        classmethod(fake_iter),
    )

    resp = web_client.get("/admin/cache/_TestCachedQuery")
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# /admin/cache/<query_class_name>/<cache_key>  (info + delete)
# ---------------------------------------------------------------------------


def test_cached_query_info_not_found(
    web_client: Client, login_gae_admin, ndb_stub
) -> None:
    resp = web_client.get("/admin/cache/_TestCachedQuery/test_admin_cache_a:1:1")
    assert resp.status_code == 404


def test_cached_query_info(web_client: Client, login_gae_admin, ndb_stub) -> None:
    cache_key = _make_cache_key("test_admin_cache_a", 1, 1)
    CachedQueryResult(id=cache_key, result=None).put()

    resp = web_client.get(f"/admin/cache/_TestCachedQuery/{cache_key}")
    assert resp.status_code == 200
    body = resp.data.decode()
    assert f"CachedQueryResult: {cache_key}" in body
    assert f"/admin/cache/_TestCachedQuery/{cache_key}/delete" in body


def test_cached_query_delete_not_found(
    web_client: Client, login_gae_admin, ndb_stub
) -> None:
    resp = web_client.get("/admin/cache/_TestCachedQuery/test_admin_cache_a:1:1/delete")
    assert resp.status_code == 404


def test_cached_query_delete(web_client: Client, login_gae_admin, ndb_stub) -> None:
    cache_key = _make_cache_key("test_admin_cache_a", 1, 1)
    CachedQueryResult(id=cache_key, result=None).put()

    resp = web_client.get(f"/admin/cache/_TestCachedQuery/{cache_key}/delete")
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/admin/cache/_TestCachedQuery"
    assert CachedQueryResult.get_by_id(cache_key) is None


# ---------------------------------------------------------------------------
# /admin/cache/clear/<model_type>/<model_key>
# ---------------------------------------------------------------------------


def test_clear_model_cache_event(
    web_client: Client, login_gae_admin, ndb_stub, taskqueue_stub
) -> None:
    Event(
        id="2020nyny",
        event_short="nyny",
        year=2020,
        event_type_enum=EventType.REGIONAL,
    ).put()
    EventDetails(id="2020nyny").put()

    with (
        patch.object(EventManipulator, "clearCache") as mock_event_clear,
        patch.object(EventDetailsManipulator, "clearCache") as mock_details_clear,
    ):
        resp = web_client.get("/admin/cache/clear/event/2020nyny")

    assert resp.status_code == 302
    assert resp.headers["Location"] == "/admin/event/2020nyny"
    mock_event_clear.assert_called_once()
    assert mock_event_clear.call_args[0][0].key_name == "2020nyny"
    mock_details_clear.assert_called_once()
    assert mock_details_clear.call_args[0][0].key_name == "2020nyny"


def test_clear_model_cache_event_not_found(
    web_client: Client, login_gae_admin, ndb_stub
) -> None:
    resp = web_client.get("/admin/cache/clear/event/2020nyny")
    assert resp.status_code == 404


def test_clear_model_cache_match(
    web_client: Client, login_gae_admin, ndb_stub, taskqueue_stub
) -> None:
    Match(
        id="2020nyny_qm1",
        event=ndb.Key(Event, "2020nyny"),
        year=2020,
        comp_level=CompLevel.QM,
        set_number=1,
        match_number=1,
        alliances_json="{}",
    ).put()

    with patch.object(MatchManipulator, "clearCache") as mock_clear:
        resp = web_client.get("/admin/cache/clear/match/2020nyny_qm1")

    assert resp.status_code == 302
    assert resp.headers["Location"] == "/admin/match/2020nyny_qm1"
    mock_clear.assert_called_once()
    assert mock_clear.call_args[0][0].key_name == "2020nyny_qm1"


def test_clear_model_cache_match_not_found(
    web_client: Client, login_gae_admin, ndb_stub
) -> None:
    resp = web_client.get("/admin/cache/clear/match/2020nyny_qm1")
    assert resp.status_code == 404


def test_clear_model_cache_team_not_found(
    web_client: Client, login_gae_admin, ndb_stub
) -> None:
    resp = web_client.get("/admin/cache/clear/team/frc254")
    assert resp.status_code == 404


def test_clear_model_cache_unknown_type_redirects_home(
    web_client: Client, login_gae_admin, ndb_stub
) -> None:
    resp = web_client.get("/admin/cache/clear/district/2020ne")
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/admin/"


def test_clear_event_cache_without_details_redirects_to_event_page(
    web_client: Client, login_gae_admin, ndb_stub, taskqueue_stub
) -> None:
    """An event without EventDetails still has its cache cleared and redirects."""
    Event(
        id="2020nyny",
        event_short="nyny",
        year=2020,
        event_type_enum=EventType.REGIONAL,
    ).put()

    with patch.object(EventManipulator, "clearCache") as mock_event_clear:
        resp = web_client.get("/admin/cache/clear/event/2020nyny")

    assert resp.status_code == 302
    assert resp.headers["Location"] == "/admin/event/2020nyny"
    mock_event_clear.assert_called_once()


def test_clear_team_cache_redirects_to_team_page(
    web_client: Client, login_gae_admin, ndb_stub, taskqueue_stub
) -> None:
    """Clearing a team's cache redirects to its admin page."""
    Team(id="frc254", team_number=254).put()

    with patch.object(TeamManipulator, "clearCache") as mock_clear:
        resp = web_client.get("/admin/cache/clear/team/frc254")

    assert resp.status_code == 302
    assert resp.headers["Location"] == "/admin/team/254"
    mock_clear.assert_called_once()
    assert mock_clear.call_args[0][0].key_name == "frc254"


def test_purge_orphans_defaults_to_dry_run(
    web_client: Client, login_gae_admin, ndb_stub, taskqueue_stub
) -> None:
    current_v = CachedDatabaseQuery.DATABASE_QUERY_VERSION
    orphan_key = _make_cache_key("test_admin_cache_a", 1, current_v - 2)
    CachedQueryResult(id=orphan_key, result=None).put()

    resp = web_client.post("/admin/cache/purge_orphans")
    assert resp.status_code == 302

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="cache-clearing")
    assert len(tasks) == 1
    run_from_task(tasks[0])
    assert CachedQueryResult.get_by_id(orphan_key) is not None


def test_purge_orphans_execute_deletes_orphans(
    web_client: Client, login_gae_admin, ndb_stub, taskqueue_stub
) -> None:
    current_v = CachedDatabaseQuery.DATABASE_QUERY_VERSION
    orphan_key = _make_cache_key("test_admin_cache_a", 1, current_v - 2)
    current_key = _make_cache_key("test_admin_cache_b", 1, current_v)
    CachedQueryResult(id=orphan_key, result=None).put()
    CachedQueryResult(id=current_key, result=None).put()

    resp = web_client.post("/admin/cache/purge_orphans", data={"execute": "true"})
    assert resp.status_code == 302

    for task in taskqueue_stub.get_filtered_tasks(queue_names="cache-clearing"):
        run_from_task(task)
    assert CachedQueryResult.get_by_id(orphan_key) is None
    assert CachedQueryResult.get_by_id(current_key) is not None


def test_purge_orphans_not_accessible_without_login(
    web_client: Client, ndb_stub
) -> None:
    resp = web_client.post("/admin/cache/purge_orphans")
    assert resp.status_code == 401
