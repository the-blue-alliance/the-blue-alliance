from unittest.mock import MagicMock

import pytest
from google.appengine.ext import ndb
from pyre_extensions import none_throws
from werkzeug.test import Client

from backend.api.handlers.helpers.etag_helper import (
    get_etag_dependencies,
    normalize_etag,
)
from backend.common.consts.auth_type import AuthType
from backend.common.environment import Environment
from backend.common.memcache import MemcacheClient
from backend.common.models.api_auth_access import ApiAuthAccess
from backend.common.models.award import Award
from backend.common.models.event import Event
from backend.common.models.event_team import EventTeam
from backend.common.models.team import Team
from backend.common.queries.award_query import TeamAwardsQuery
from backend.common.queries.team_query import TeamQuery


def test_validate_etag_records_and_short_circuits_304(
    ndb_stub, api_client: Client, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Disable flask_response_cache to specifically test the @validate_etag fast path
    monkeypatch.setattr(Environment, "flask_response_cache_enabled", lambda: False)

    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    Team(id="frc254", team_number=254, nickname="The Cheesy Poofs").put()

    # 1. First request: cache miss, executes validate_keys and handler, records query in Memcache
    resp1 = api_client.get(
        "/api/v3/team/frc254", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp1.status_code == 200
    assert resp1.json["key"] == "frc254"
    etag = resp1.headers.get("ETag")
    assert etag is not None

    normalized_etag = normalize_etag(etag)
    assert normalized_etag is not None
    deps = get_etag_dependencies(normalized_etag, path="/api/v3/team/frc254")
    assert deps is not None
    assert any("frc254" in k for k in deps.keys())

    # Mock Team.get_by_id_async to verify handler and validate_keys are completely bypassed
    original_get_by_id_async = Team.get_by_id_async
    mock_get_by_id_async = MagicMock(side_effect=original_get_by_id_async)
    monkeypatch.setattr(Team, "get_by_id_async", mock_get_by_id_async)

    # 2. Second request with If-None-Match: should return 304 via @validate_etag fast path
    resp2 = api_client.get(
        "/api/v3/team/frc254",
        headers={"X-TBA-Auth-Key": "test_auth_key", "If-None-Match": etag},
    )
    assert resp2.status_code == 304
    assert resp2.headers.get("ETag") == etag
    mock_get_by_id_async.assert_not_called()


def test_delete_cache_multi_invalidates_etag_304(
    ndb_stub, api_client: Client, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(Environment, "flask_response_cache_enabled", lambda: False)

    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    team_obj = Team(id="frc254", team_number=254, nickname="The Cheesy Poofs")
    team_obj.put()

    # Initial request
    resp1 = api_client.get(
        "/api/v3/team/frc254", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp1.status_code == 200
    etag = resp1.headers.get("ETag")
    assert etag is not None

    # Verify 304 works
    resp2 = api_client.get(
        "/api/v3/team/frc254",
        headers={"X-TBA-Auth-Key": "test_auth_key", "If-None-Match": etag},
    )
    assert resp2.status_code == 304

    # Update team and invalidate cache
    team_obj.nickname = "Updated Poofs"
    team_obj.put()
    TeamQuery.delete_cache_multi({TeamQuery(team_key="frc254").cache_key})

    # Next request with old ETag should NOT return 304, but fresh 200 with new data
    resp3 = api_client.get(
        "/api/v3/team/frc254",
        headers={"X-TBA-Auth-Key": "test_auth_key", "If-None-Match": etag},
    )
    assert resp3.status_code == 200
    assert resp3.json["nickname"] == "Updated Poofs"
    new_etag = resp3.headers.get("ETag")
    assert new_etag != etag


def test_validate_etag_multi_query_endpoint(
    ndb_stub, api_client: Client, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(Environment, "flask_response_cache_enabled", lambda: False)

    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    Team(id="frc254", team_number=254).put()
    Event(id="2020casj", year=2020, event_short="casj", event_type_enum=0).put()
    event_key = none_throws(Event.get_by_id("2020casj")).key
    team_key = none_throws(Team.get_by_id("frc254")).key
    EventTeam(
        id="2020casj_frc254",
        event=event_key,
        team=team_key,
        year=2020,
    ).put()
    award = Award(
        id="2020casj_1",
        year=2020,
        award_type_enum=1,
        event_type_enum=0,
        event=event_key,
        name_str="Winner",
        team_list=[team_key],
        recipient_json_list=[],
    )
    award.put()

    # First request to team history (fetches TeamEventsQuery and TeamAwardsQuery)
    resp1 = api_client.get(
        "/api/v3/team/frc254/history", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp1.status_code == 200
    etag = resp1.headers.get("ETag")
    assert etag is not None

    normalized_etag = normalize_etag(etag)
    assert normalized_etag is not None
    deps = get_etag_dependencies(normalized_etag, path="/api/v3/team/frc254/history")
    assert deps is not None
    assert len(deps) >= 2  # Must contain events and awards query keys

    # Verify 304 returns
    resp2 = api_client.get(
        "/api/v3/team/frc254/history",
        headers={"X-TBA-Auth-Key": "test_auth_key", "If-None-Match": etag},
    )
    assert resp2.status_code == 304

    # Update award data and invalidate ONLY TeamAwardsQuery
    award.name_str = "Finalist"
    award.put()
    TeamAwardsQuery.delete_cache_multi({TeamAwardsQuery(team_key="frc254").cache_key})

    # Next request with old ETag must return 200 because one dependent query was invalidated
    resp3 = api_client.get(
        "/api/v3/team/frc254/history",
        headers={"X-TBA-Auth-Key": "test_auth_key", "If-None-Match": etag},
    )
    assert resp3.status_code == 200
    assert resp3.json["awards"][0]["name"] == "Finalist"


def test_scoped_etag_deps_prevent_cross_endpoint_collision(
    ndb_stub, api_client: Client, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    Ensure that when two different endpoints return identical responses (e.g. empty lists []),
    their ETag dependency mappings are scoped by endpoint path and do not overwrite each other.
    """
    monkeypatch.setattr(Environment, "flask_response_cache_enabled", lambda: False)

    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    Team(id="frc254", team_number=254).put()
    Team(id="frc9999", team_number=9999).put()
    Event(id="2020casj", year=2020, event_short="casj", event_type_enum=0).put()

    # 1. Both endpoints return [] and generate the exact same ETag
    resp_254 = api_client.get(
        "/api/v3/team/frc254/awards", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    resp_9999 = api_client.get(
        "/api/v3/team/frc9999/awards", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp_254.status_code == 200
    assert resp_9999.status_code == 200
    assert resp_254.json == []
    assert resp_9999.json == []

    etag_254 = resp_254.headers.get("ETag")
    etag_9999 = resp_9999.headers.get("ETag")
    assert etag_254 == etag_9999  # Identical payload produces identical ETag hash

    # Both endpoints should have separate dependency records in Memcache
    norm_etag = normalize_etag(etag_254)
    assert norm_etag is not None
    deps_254 = get_etag_dependencies(norm_etag, path="/api/v3/team/frc254/awards")
    deps_9999 = get_etag_dependencies(norm_etag, path="/api/v3/team/frc9999/awards")
    assert deps_254 is not None
    assert deps_9999 is not None
    assert any("frc254" in k for k in deps_254.keys())
    assert any("frc9999" in k for k in deps_9999.keys())

    # 2. Add an award to frc254 and invalidate only frc254's awards query
    Award(
        id="2020casj_1",
        year=2020,
        award_type_enum=1,
        event_type_enum=0,
        event=none_throws(Event.get_by_id("2020casj")).key,
        name_str="Winner",
        team_list=[none_throws(Team.get_by_id("frc254")).key],
        recipient_json_list=[],
    ).put()
    TeamAwardsQuery.delete_cache_multi({TeamAwardsQuery(team_key="frc254").cache_key})

    # 3. frc254 request with old ETag must return 200 with new data
    resp_254_updated = api_client.get(
        "/api/v3/team/frc254/awards",
        headers={"X-TBA-Auth-Key": "test_auth_key", "If-None-Match": etag_254},
    )
    assert resp_254_updated.status_code == 200
    assert len(resp_254_updated.json) == 1

    # 4. frc9999 request with the same empty-list ETag must STILL return 304!
    resp_9999_fresh = api_client.get(
        "/api/v3/team/frc9999/awards",
        headers={"X-TBA-Auth-Key": "test_auth_key", "If-None-Match": etag_9999},
    )
    assert resp_9999_fresh.status_code == 304


def test_validate_etag_unauthenticated_request_rejected(
    ndb_stub, api_client: Client
) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    Team(id="frc254", team_number=254).put()

    resp1 = api_client.get(
        "/api/v3/team/frc254", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    etag = resp1.headers.get("ETag")

    # Request without auth must return 401 even with If-None-Match
    resp_unauth = api_client.get("/api/v3/team/frc254", headers={"If-None-Match": etag})
    assert resp_unauth.status_code == 401


def test_validate_etag_fallback_on_memcache_error(
    ndb_stub, api_client: Client, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(Environment, "flask_response_cache_enabled", lambda: False)

    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    Team(id="frc254", team_number=254).put()

    # Initial request
    resp1 = api_client.get(
        "/api/v3/team/frc254", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    etag = resp1.headers.get("ETag")

    # Track handler execution via Team.get_by_id_async
    original_get_by_id_async = Team.get_by_id_async
    mock_get_by_id_async = MagicMock(side_effect=original_get_by_id_async)
    monkeypatch.setattr(Team, "get_by_id_async", mock_get_by_id_async)

    # Simulate Memcache failure during validation
    monkeypatch.setattr(
        MemcacheClient.get(),
        "get",
        MagicMock(side_effect=Exception("Memcache timeout")),
    )

    # Request should gracefully execute the handler without crashing
    resp2 = api_client.get(
        "/api/v3/team/frc254",
        headers={"X-TBA-Auth-Key": "test_auth_key", "If-None-Match": etag},
    )
    assert resp2.status_code in (200, 304)
    # Handler must have run (not fast-path short-circuited)
    mock_get_by_id_async.assert_called()


def test_event_alliances_etag_invalidated_on_event_team_update(
    ndb_stub, api_client: Client, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(Environment, "flask_response_cache_enabled", lambda: False)

    from backend.common.consts.comp_level import CompLevel
    from backend.common.models.alliance import PlayoffAllianceStatus, PlayoffOutcome
    from backend.common.models.event_details import EventDetails
    from backend.common.models.event_team_status import (
        EventTeamStatus,
        EventTeamStatusAlliance,
    )
    from backend.common.queries.team_query import EventEventTeamsQuery

    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    Event(id="2020casj", year=2020, event_short="casj", event_type_enum=0).put()
    Team(id="frc254", team_number=254).put()
    Team(id="frc971", team_number=971).put()

    EventDetails(
        id="2020casj",
        alliance_selections=[{"picks": ["frc254", "frc971"], "declines": []}],
    ).put()

    event_team = EventTeam(
        id="2020casj_frc254",
        event=ndb.Key(Event, "2020casj"),
        team=ndb.Key(Team, "frc254"),
        year=2020,
        status=EventTeamStatus(
            qual=None,
            playoff=PlayoffAllianceStatus(
                level=CompLevel.QF,
                status=PlayoffOutcome.PLAYING,
                current_level_record=None,
                record=None,
            ),
            alliance=EventTeamStatusAlliance(name=None, number=1, pick=0, backup=None),
            last_match_key=None,
            next_match_key=None,
        ),
    )
    event_team.put()

    # Initial request
    resp1 = api_client.get(
        "/api/v3/event/2020casj/alliances",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp1.status_code == 200
    assert resp1.json[0]["status"]["status"] == "playing"
    etag = resp1.headers.get("ETag")
    assert etag is not None

    # Should 304 with unchanged ETag
    resp2 = api_client.get(
        "/api/v3/event/2020casj/alliances",
        headers={"X-TBA-Auth-Key": "test_auth_key", "If-None-Match": etag},
    )
    assert resp2.status_code == 304

    # Update event team playoff status and invalidate EventEventTeamsQuery
    status = none_throws(event_team.status)
    none_throws(status["playoff"])["status"] = PlayoffOutcome.WON
    event_team.put()

    EventEventTeamsQuery.delete_cache_multi(
        {EventEventTeamsQuery(event_key="2020casj").cache_key}
    )

    # Should NOT 304 anymore, should return fresh 200 with new status
    resp3 = api_client.get(
        "/api/v3/event/2020casj/alliances",
        headers={"X-TBA-Auth-Key": "test_auth_key", "If-None-Match": etag},
    )
    assert resp3.status_code == 200
    assert resp3.json[0]["status"]["status"] == "won"
    assert resp3.headers.get("ETag") != etag


def test_event_playoff_advancement_etag_invalidated_on_event_details_update(
    ndb_stub, api_client: Client, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(Environment, "flask_response_cache_enabled", lambda: False)

    from backend.common.helpers.playoff_advancement_helper import (
        PlayoffAdvancementHelper,
    )
    from backend.common.models.event_details import EventDetails
    from backend.common.queries.event_details_query import EventDetailsQuery

    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    Event(
        id="2020casj",
        year=2020,
        event_short="casj",
        event_type_enum=0,
        playoff_type=0,
    ).put()
    event_details = EventDetails(
        id="2020casj",
        playoff_advancement={"bracket": {}, "advancement": {}},
    )
    event_details.put()

    # Initial request
    resp1 = api_client.get(
        "/api/v3/event/2020casj/playoff_advancement",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp1.status_code == 200
    etag = resp1.headers.get("ETag")
    assert etag is not None

    # Verify that point queries with MODEL_CACHING_ENABLED = False are tracked
    deps = get_etag_dependencies(
        none_throws(normalize_etag(etag)),
        path="/api/v3/event/2020casj/playoff_advancement",
    )
    assert deps is not None
    assert any("event_details_2020casj" in k for k in deps.keys())
    assert any("event_2020casj" in k for k in deps.keys())

    # Should 304 with unchanged ETag
    resp2 = api_client.get(
        "/api/v3/event/2020casj/playoff_advancement",
        headers={"X-TBA-Auth-Key": "test_auth_key", "If-None-Match": etag},
    )
    assert resp2.status_code == 304

    # Update EventDetails (which has MODEL_CACHING_ENABLED = False)
    # and invalidate EventDetailsQuery
    monkeypatch.setattr(
        PlayoffAdvancementHelper,
        "create_playoff_advancement_response_for_apiv3",
        lambda *args, **kwargs: [{"mock_advancement": "updated"}],
    )
    EventDetailsQuery.delete_cache_multi(
        {EventDetailsQuery(event_key="2020casj").cache_key}
    )

    # Should NOT 304 anymore, should return fresh 200 with new playoff advancement
    resp3 = api_client.get(
        "/api/v3/event/2020casj/playoff_advancement",
        headers={"X-TBA-Auth-Key": "test_auth_key", "If-None-Match": etag},
    )
    assert resp3.status_code == 200
    assert resp3.json == [{"mock_advancement": "updated"}]
    assert resp3.headers.get("ETag") != etag


def test_search_index_etag_invalidated_on_new_team_page(
    ndb_stub, api_client: Client, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(Environment, "flask_response_cache_enabled", lambda: False)

    from backend.common.queries.team_query import TeamListQuery

    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    Team(id="frc254", team_number=254, nickname="The Cheesy Poofs").put()

    # Initial request (max team is 254 -> max_team_page = 0, watches page 0 and 1)
    resp1 = api_client.get(
        "/api/v3/search_index",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp1.status_code == 200
    etag = resp1.headers.get("ETag")
    assert etag is not None
    assert len(resp1.json["teams"]) == 1

    # Should 304 with unchanged ETag
    resp2 = api_client.get(
        "/api/v3/search_index",
        headers={"X-TBA-Auth-Key": "test_auth_key", "If-None-Match": etag},
    )
    assert resp2.status_code == 304

    # Create team on page 1 (team 600) and invalidate TeamListQuery(page=1)
    Team(id="frc600", team_number=600, nickname="Team 600").put()
    TeamListQuery.delete_cache_multi({TeamListQuery(page=1).cache_key})

    # Should NOT 304, should return fresh 200 with team 600
    resp3 = api_client.get(
        "/api/v3/search_index",
        headers={"X-TBA-Auth-Key": "test_auth_key", "If-None-Match": etag},
    )
    assert resp3.status_code == 200
    assert len(resp3.json["teams"]) == 2
    assert resp3.headers.get("ETag") != etag


def test_team_list_all_etag_invalidated_on_new_team_page(
    ndb_stub, api_client: Client, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(Environment, "flask_response_cache_enabled", lambda: False)

    from backend.common.queries.team_query import TeamListQuery

    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    Team(id="frc254", team_number=254, nickname="The Cheesy Poofs").put()

    # Initial request (max team is 254 -> max_team_page = 0, watches page 0 and 1)
    resp1 = api_client.get(
        "/api/v3/teams/all",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp1.status_code == 200
    etag = resp1.headers.get("ETag")
    assert etag is not None
    assert len(resp1.json) == 1

    # Should 304 with unchanged ETag
    resp2 = api_client.get(
        "/api/v3/teams/all",
        headers={"X-TBA-Auth-Key": "test_auth_key", "If-None-Match": etag},
    )
    assert resp2.status_code == 304

    # Create team on page 1 (team 600) and invalidate TeamListQuery(page=1)
    Team(id="frc600", team_number=600, nickname="Team 600").put()
    TeamListQuery.delete_cache_multi({TeamListQuery(page=1).cache_key})

    # Should NOT 304, should return fresh 200 with team 600
    resp3 = api_client.get(
        "/api/v3/teams/all",
        headers={"X-TBA-Auth-Key": "test_auth_key", "If-None-Match": etag},
    )
    assert resp3.status_code == 200
    assert len(resp3.json) == 2
    assert resp3.headers.get("ETag") != etag


def test_validate_etag_weak_etag_supported(
    ndb_stub, api_client: Client, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(Environment, "flask_response_cache_enabled", lambda: False)

    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    Team(id="frc254", team_number=254, nickname="The Cheesy Poofs").put()

    # Initial request
    resp1 = api_client.get(
        "/api/v3/team/frc254", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp1.status_code == 200
    etag = resp1.headers.get("ETag")
    assert etag is not None

    # Track handler calls via Team.get_by_id_async
    original_get_by_id_async = Team.get_by_id_async
    mock_get_by_id_async = MagicMock(side_effect=original_get_by_id_async)
    monkeypatch.setattr(Team, "get_by_id_async", mock_get_by_id_async)

    # Sending weak ETag (e.g. W/"<hash>") should short-circuit to 304
    weak_etag = f"W/{etag}"
    resp2 = api_client.get(
        "/api/v3/team/frc254",
        headers={"X-TBA-Auth-Key": "test_auth_key", "If-None-Match": weak_etag},
    )
    assert resp2.status_code == 304
    assert resp2.headers.get("ETag") == etag
    mock_get_by_id_async.assert_not_called()
