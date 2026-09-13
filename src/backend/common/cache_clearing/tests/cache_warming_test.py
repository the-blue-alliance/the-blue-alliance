from unittest.mock import patch

import orjson

from backend.common.cache_clearing.cache_warming import warm_cache_queries
from backend.common.consts.api_version import ApiMajorVersion
from backend.common.consts.event_type import EventType
from backend.common.helpers.deferred import run_from_task
from backend.common.manipulators.event_manipulator import EventManipulator
from backend.common.manipulators.team_manipulator import TeamManipulator
from backend.common.models.cached_query_result import CachedQueryResult
from backend.common.models.event import Event
from backend.common.models.team import Team
from backend.common.queries.database_query import CachedDatabaseQuery
from backend.common.queries.district_query import DistrictQuery, DistrictsInYearQuery
from backend.common.queries.event_query import (
    DistrictEventsQuery,
    EventListQuery,
    EventQuery,
)
from backend.common.queries.team_query import (
    DistrictTeamsQuery,
    TeamListQuery,
    TeamListYearQuery,
    TeamQuery,
)


def test_from_cache_key_bulk_queries() -> None:
    # EventListQuery
    q_event_list = EventListQuery.from_cache_key("event_list_2026:4:6")
    assert q_event_list is not None
    assert isinstance(q_event_list, EventListQuery)
    assert q_event_list._query_args == {"year": 2026}
    assert q_event_list.cache_key == "event_list_2026:4:6"

    # EventListQuery from dict cache key
    q_event_list_dict = EventListQuery.from_cache_key("event_list_2026:4:6~dictv3.9")
    assert q_event_list_dict is not None
    assert isinstance(q_event_list_dict, EventListQuery)
    assert q_event_list_dict._query_args == {"year": 2026}

    # TeamListYearQuery
    q_team_list_year = TeamListYearQuery.from_cache_key("team_list_year_2026_0:2:6")
    assert q_team_list_year is not None
    assert isinstance(q_team_list_year, TeamListYearQuery)
    assert q_team_list_year._query_args == {"year": 2026, "page": 0}
    assert q_team_list_year.cache_key == "team_list_year_2026_0:2:6"

    # TeamListQuery
    q_team_list = TeamListQuery.from_cache_key("team_list_1:2:6")
    assert q_team_list is not None
    assert isinstance(q_team_list, TeamListQuery)
    assert q_team_list._query_args == {"page": 1}
    assert q_team_list.cache_key == "team_list_1:2:6"

    # DistrictsInYearQuery
    q_districts_year = DistrictsInYearQuery.from_cache_key("districts_in_year_2026:0:6")
    assert q_districts_year is not None
    assert isinstance(q_districts_year, DistrictsInYearQuery)
    assert q_districts_year._query_args == {"year": 2026}
    assert q_districts_year.cache_key == "districts_in_year_2026:0:6"

    # DistrictEventsQuery
    q_district_events = DistrictEventsQuery.from_cache_key(
        "district_events_2026fim:5:6"
    )
    assert q_district_events is not None
    assert isinstance(q_district_events, DistrictEventsQuery)
    assert q_district_events._query_args == {"district_key": "2026fim"}
    assert q_district_events.cache_key == "district_events_2026fim:5:6"

    # DistrictTeamsQuery
    q_district_teams = DistrictTeamsQuery.from_cache_key("district_teams_2026fim:3:6")
    assert q_district_teams is not None
    assert isinstance(q_district_teams, DistrictTeamsQuery)
    assert q_district_teams._query_args == {"district_key": "2026fim"}
    assert q_district_teams.cache_key == "district_teams_2026fim:3:6"


def test_from_cache_key_invalid_or_mismatched() -> None:
    # Key doesn't match format
    assert EventListQuery.from_cache_key("wrong_format_2026:4:6") is None
    # Empty key format
    assert CachedDatabaseQuery.from_cache_key("anything:1:1") is None


def test_cache_on_write_enabled_flags() -> None:
    # Bulk season queries should have CACHE_ON_WRITE_ENABLED = True
    assert EventListQuery.CACHE_ON_WRITE_ENABLED is True
    assert DistrictEventsQuery.CACHE_ON_WRITE_ENABLED is True
    assert TeamListYearQuery.CACHE_ON_WRITE_ENABLED is True
    assert TeamListQuery.CACHE_ON_WRITE_ENABLED is True
    assert DistrictTeamsQuery.CACHE_ON_WRITE_ENABLED is True
    assert DistrictsInYearQuery.CACHE_ON_WRITE_ENABLED is True

    # Point queries should have CACHE_ON_WRITE_ENABLED = False
    assert EventQuery.CACHE_ON_WRITE_ENABLED is False
    assert TeamQuery.CACHE_ON_WRITE_ENABLED is False
    assert DistrictQuery.CACHE_ON_WRITE_ENABLED is False
    assert CachedDatabaseQuery.CACHE_ON_WRITE_ENABLED is False


def test_warm_cache_queries_empty() -> None:
    # Empty list should succeed without error
    warm_cache_queries([])


def test_warm_cache_queries_populates_json_bytes(ndb_context) -> None:
    Event(
        id="2026casf",
        year=2026,
        event_type_enum=EventType.REGIONAL,
        event_short="casf",
        name="San Francisco Regional",
    ).put()

    q = EventListQuery(year=2026)
    dict_cache_key = q.dict_cache_key(ApiMajorVersion.API_V3)

    # Initial state: cache is cold
    assert CachedQueryResult.get_by_id(dict_cache_key) is None

    # Warm cache
    warm_cache_queries([q])

    # Cache is now warm with pre-serialized JSON bytes
    cqr = CachedQueryResult.get_by_id(dict_cache_key)
    assert cqr is not None
    json_bytes = cqr.get_json_bytes()
    assert json_bytes is not None
    parsed = orjson.loads(json_bytes)
    assert len(parsed) == 1
    assert parsed[0]["key"] == "2026casf"

    # Subsequent fetch_json hits the warm cache without query
    with patch.object(q, "_query_async") as mock_query:
        hit_bytes = q.fetch_json(ApiMajorVersion.API_V3)
        assert hit_bytes == json_bytes
        mock_query.assert_not_called()

    # Subsequent fetch_dict hits the warm cache without query
    with patch.object(q, "_query_async") as mock_query:
        hit_dict = q.fetch_dict(ApiMajorVersion.API_V3)
        assert hit_dict == parsed
        mock_query.assert_not_called()


def test_warm_cache_queries_handles_error(ndb_context) -> None:
    q = EventListQuery(year=2026)

    # Mock fetch_json_async to raise an error
    with patch.object(q, "fetch_json_async", side_effect=Exception("Datastore error")):
        # Should not raise exception
        warm_cache_queries([q])


def test_event_manipulator_cache_on_write(ndb_context, taskqueue_stub) -> None:
    event = Event(
        id="2026casf",
        year=2026,
        event_type_enum=EventType.REGIONAL,
        event_short="casf",
        name="San Francisco Regional",
    )
    EventManipulator.createOrUpdate(event)

    # _clearCache enqueued a task on cache-clearing
    tasks = taskqueue_stub.get_filtered_tasks(queue_names="cache-clearing")
    assert len(tasks) == 1
    clear_cache_task = tasks[0]

    # Run _clearCacheDeferred manually
    run_from_task(clear_cache_task)

    # After _clearCacheDeferred runs, a warming task should be enqueued on cache-clearing
    tasks = taskqueue_stub.get_filtered_tasks(queue_names="cache-clearing")
    assert len(tasks) == 2  # clear_cache_task + warm_cache_task
    warm_task = tasks[1]

    # Before running the warming task, dict cache is cold (deleted)
    q = EventListQuery(year=2026)
    dict_cache_key = q.dict_cache_key(ApiMajorVersion.API_V3)
    assert CachedQueryResult.get_by_id(dict_cache_key) is None

    # Run warm_cache_queries task
    run_from_task(warm_task)

    # Dict cache is now warm with pre-serialized JSON bytes!
    cqr = CachedQueryResult.get_by_id(dict_cache_key)
    assert cqr is not None
    json_bytes = cqr.get_json_bytes()
    assert json_bytes is not None
    parsed = orjson.loads(json_bytes)
    assert len(parsed) == 1
    assert parsed[0]["key"] == "2026casf"


def test_team_manipulator_cache_on_write(ndb_context, taskqueue_stub) -> None:
    team = Team(
        id="frc254",
        team_number=254,
        nickname="The Cheesy Poofs",
    )
    TeamManipulator.createOrUpdate(team)

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="cache-clearing")
    assert len(tasks) == 1
    clear_cache_task = tasks[0]

    # Run _clearCacheDeferred
    run_from_task(clear_cache_task)

    # Verify warming task was enqueued
    tasks = taskqueue_stub.get_filtered_tasks(queue_names="cache-clearing")
    assert len(tasks) == 2
    warm_task = tasks[1]

    # Run warming task
    run_from_task(warm_task)

    # TeamListQuery(page=0) dict cache should now be warm!
    q = TeamListQuery(page=0)
    dict_cache_key = q.dict_cache_key(ApiMajorVersion.API_V3)
    cqr = CachedQueryResult.get_by_id(dict_cache_key)
    assert cqr is not None
    json_bytes = cqr.get_json_bytes()
    assert json_bytes is not None
    parsed = orjson.loads(json_bytes)
    assert any(t["key"] == "frc254" for t in parsed)
