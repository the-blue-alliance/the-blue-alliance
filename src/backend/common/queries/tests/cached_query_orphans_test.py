from typing import List

import pytest
from google.appengine.ext import ndb, testbed

from backend.common.consts.api_version import ApiMajorVersion
from backend.common.helpers.deferred import run_from_task
from backend.common.models.cached_query_result import CachedQueryResult
from backend.common.queries.award_query import EventAwardsQuery
from backend.common.queries.cached_query_orphans import (
    all_query_classes,
    OrphanClassifier,
    parse_cache_key,
    ParsedCacheKey,
    purge_orphaned_cached_query_results,
    REASON_CACHE_VERSION,
    REASON_DB_VERSION,
    REASON_DICT_SUBVERSION,
)
from backend.common.queries.database_query import CachedDatabaseQuery
from backend.common.queries.event_query import EventQuery
from backend.common.queries.team_query import TeamQuery

DB = CachedDatabaseQuery.DATABASE_QUERY_VERSION
V3 = ApiMajorVersion.API_V3


def _sub(query_class) -> int:
    return query_class.DICT_CONVERTER.SUBVERSIONS[V3]


@pytest.fixture
def classifier() -> OrphanClassifier:
    return OrphanClassifier(all_query_classes())


def test_parse_cache_key() -> None:
    assert parse_cache_key("team_frc254:2:6") == ParsedCacheKey(
        "team_frc254", 2, 6, None
    )
    assert parse_cache_key("team_frc254:2:6~dictv3.5") == ParsedCacheKey(
        "team_frc254", 2, 6, (3, 5)
    )


@pytest.mark.parametrize(
    "key",
    [
        "",
        "no_versions",
        "team_frc254:2",
        "team_frc254:x:6",
        ":2:6",
        "team_frc254:2:6~v3",
    ],
)
def test_parse_cache_key_rejects_malformed(key: str) -> None:
    assert parse_cache_key(key) is None


def test_all_query_classes_finds_every_query_module() -> None:
    names = {c.__name__ for c in all_query_classes()}
    assert {"TeamQuery", "EventQuery", "EventAwardsQuery"} <= names


def test_current_generation_kept(classifier: OrphanClassifier) -> None:
    for query_class in all_query_classes():
        partial = query_class.CACHE_KEY_FORMAT.replace("{", "").replace("}", "")
        key = f"{partial}:{query_class.CACHE_VERSION}:{DB}"
        assert classifier.orphan_reason(key) is None, key
        if getattr(query_class, "DICT_CONVERTER", None) is not None:
            assert classifier.orphan_reason(f"{key}~dictv3.{_sub(query_class)}") is None


def test_real_cache_keys_kept(classifier: OrphanClassifier) -> None:
    for query in (TeamQuery(team_key="frc254"), EventQuery(event_key="2024casj")):
        assert classifier.orphan_reason(query.cache_key) is None
        assert classifier.orphan_reason(query.dict_cache_key(V3)) is None


def test_one_generation_behind_kept(classifier: OrphanClassifier) -> None:
    v = TeamQuery.CACHE_VERSION
    assert classifier.orphan_reason(f"team_frc254:{v}:{DB - 1}") is None
    assert classifier.orphan_reason(f"team_frc254:{v - 1}:{DB}") is None
    assert (
        classifier.orphan_reason(f"team_frc254:{v}:{DB}~dictv3.{_sub(TeamQuery) - 1}")
        is None
    )


def test_newer_generation_kept(classifier: OrphanClassifier) -> None:
    assert (
        classifier.orphan_reason(f"team_frc254:{TeamQuery.CACHE_VERSION + 1}:{DB + 1}")
        is None
    )


def test_old_db_version_orphaned(classifier: OrphanClassifier) -> None:
    assert (
        classifier.orphan_reason(f"team_frc254:{TeamQuery.CACHE_VERSION}:{DB - 2}")
        == REASON_DB_VERSION
    )
    assert classifier.orphan_reason(f"removed_query_x:0:{DB - 2}") == REASON_DB_VERSION


def test_old_cache_version_orphaned(classifier: OrphanClassifier) -> None:
    key = f"team_frc254:{TeamQuery.CACHE_VERSION - 2}:{DB}"
    assert classifier.orphan_reason(key) == REASON_CACHE_VERSION


def test_old_dict_subversion_orphaned(classifier: OrphanClassifier) -> None:
    key = f"team_frc254:{TeamQuery.CACHE_VERSION}:{DB}~dictv3.{_sub(TeamQuery) - 2}"
    assert classifier.orphan_reason(key) == REASON_DICT_SUBVERSION


def test_unknown_query_kept(classifier: OrphanClassifier) -> None:
    assert classifier.orphan_reason(f"removed_query_x:0:{DB}") is None


def test_unparseable_kept(classifier: OrphanClassifier) -> None:
    assert classifier.orphan_reason("team_frc254") is None
    assert classifier.orphan_reason(f"team_frc254:0:{DB - 2}~garbage") is None


def test_overlapping_prefix_uses_own_version(classifier: OrphanClassifier) -> None:
    # "event_{event_key}" also matches "event_awards_2024casj"; current for either class is kept
    assert EventQuery in classifier.matching_classes("event_awards_2024casj")
    assert EventAwardsQuery in classifier.matching_classes("event_awards_2024casj")
    for version in (EventQuery.CACHE_VERSION, EventAwardsQuery.CACHE_VERSION):
        assert classifier.orphan_reason(f"event_awards_2024casj:{version}:{DB}") is None


def test_ambiguous_key_orphaned_only_when_stale_for_all(
    classifier: OrphanClassifier,
) -> None:
    stale = min(EventQuery.CACHE_VERSION, EventAwardsQuery.CACHE_VERSION) - 2
    key = f"event_awards_2024casj:{stale}:{DB}"
    assert classifier.orphan_reason(key) == REASON_CACHE_VERSION


def _put(keys: List[str]) -> None:
    ndb.put_multi([CachedQueryResult(id=k, result=None) for k in keys])


def _drain(taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub) -> int:
    runs = 0
    while tasks := taskqueue_stub.get_filtered_tasks(queue_names="cache-clearing"):
        taskqueue_stub.FlushQueue("cache-clearing")
        for task in tasks:
            run_from_task(task)
            runs += 1
    return runs


def _keys() -> tuple[List[str], List[str]]:
    v = TeamQuery.CACHE_VERSION
    live = [
        f"team_frc254:{v}:{DB}",
        f"team_frc254:{v}:{DB}~dictv3.{_sub(TeamQuery)}",
        f"team_frc604:{v}:{DB - 1}",
        f"removed_query_x:0:{DB}",
        "not_a_cache_key",
    ]
    orphaned = [
        f"team_frc254:{v}:{DB - 2}",
        f"team_frc254:{v - 2}:{DB}",
        f"team_frc254:{v}:{DB}~dictv3.{_sub(TeamQuery) - 2}",
        f"removed_query_x:0:{DB - 3}",
    ]
    return live, orphaned


def test_purge_dry_run_deletes_nothing(ndb_stub, taskqueue_stub) -> None:
    live, orphaned = _keys()
    _put(live + orphaned)

    totals = purge_orphaned_cached_query_results(dry_run=True)

    assert totals["scanned"] == len(live) + len(orphaned)
    assert totals["kept"] == len(live)
    assert sum(v for k, v in totals.items() if k.startswith("orphaned:")) == len(
        orphaned
    )
    assert CachedQueryResult.query().count() == len(live) + len(orphaned)


def test_purge_deletes_only_orphans_across_tasks(ndb_stub, taskqueue_stub) -> None:
    live, orphaned = _keys()
    _put(live + orphaned)

    purge_orphaned_cached_query_results(dry_run=False, pages_per_task=1, page_size=2)
    assert _drain(taskqueue_stub) >= 3

    remaining = {k.string_id() for k in CachedQueryResult.query().fetch(keys_only=True)}
    assert remaining == set(live)
