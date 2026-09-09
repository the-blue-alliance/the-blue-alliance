import datetime
import time
from unittest.mock import MagicMock, patch

from google.appengine.ext import ndb
from werkzeug.test import Client

from backend.api.handlers.decorators import (
    _get_key_exists_ttl,
    key_does_not_exist_cache,
    key_exists_cache,
    KEY_EXISTS_CACHE_TTL_CURRENT_YEAR,
    KEY_EXISTS_CACHE_TTL_DEFAULT,
    validate_keys,
)
from backend.common.consts.auth_type import AuthType
from backend.common.consts.event_type import EventType
from backend.common.models.api_auth_access import ApiAuthAccess
from backend.common.models.district import District
from backend.common.models.event import Event
from backend.common.models.match import Match
from backend.common.models.team import Team


def test_validate_keys_positive_cache_hit_skips_datastore_query(
    ndb_stub, api_client: Client
) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    Team(id="frc254", team_number=254).put()

    # 1. First request queries Datastore and populates positive cache
    assert key_exists_cache.get(("Team", "frc254")) is None
    resp1 = api_client.get(
        "/api/v3/team/frc254", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp1.status_code == 200
    assert key_exists_cache.get(("Team", "frc254")) is True

    # 2. Subsequent request should hit key_exists_cache and skip Team.get_by_id_async
    with patch.object(
        Team,
        "get_by_id_async",
        side_effect=AssertionError("Should not call Team.get_by_id_async"),
    ):
        resp2 = api_client.get(
            "/api/v3/team/frc254", headers={"X-TBA-Auth-Key": "test_auth_key"}
        )
        assert resp2.status_code == 200


def test_validate_keys_negative_cache_hit_skips_datastore_query(
    ndb_stub, api_client: Client
) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()

    # 1. Nonexistent team key: returns 404 and populates negative cache
    assert key_does_not_exist_cache.get(("Team", "frc9999999")) is None
    resp1 = api_client.get(
        "/api/v3/team/frc9999999", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp1.status_code == 404
    assert resp1.json["Error"] == "team key: frc9999999 does not exist"
    assert key_does_not_exist_cache.get(("Team", "frc9999999")) is True

    # 2. Subsequent request should short-circuit via negative cache without calling Team.get_by_id_async
    with patch.object(
        Team,
        "get_by_id_async",
        side_effect=AssertionError("Should not call Team.get_by_id_async"),
    ):
        resp2 = api_client.get(
            "/api/v3/team/frc9999999", headers={"X-TBA-Auth-Key": "test_auth_key"}
        )
        assert resp2.status_code == 404
        assert resp2.json["Error"] == "team key: frc9999999 does not exist"


def test_validate_keys_negative_cache_for_all_entity_types(
    ndb_stub, api_client: Client
) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()

    # Event
    resp_event = api_client.get(
        "/api/v3/event/2020nonexistent", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp_event.status_code == 404
    assert resp_event.json["Error"] == "event key: 2020nonexistent does not exist"
    assert key_does_not_exist_cache.get(("Event", "2020nonexistent")) is True

    # Match
    resp_match = api_client.get(
        "/api/v3/match/2020casj_qm99", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp_match.status_code == 404
    assert resp_match.json["Error"] == "match key: 2020casj_qm99 does not exist"
    assert key_does_not_exist_cache.get(("Match", "2020casj_qm99")) is True

    # District
    resp_district = api_client.get(
        "/api/v3/district/2020nonexistent/rankings",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp_district.status_code == 404
    assert resp_district.json["Error"] == "district key: 2020nonexistent does not exist"
    assert key_does_not_exist_cache.get(("District", "2020nonexistent")) is True


def test_key_exists_cache_ttl_logic() -> None:
    current_year = datetime.date.today().year

    # Teams: always 24 hours
    assert _get_key_exists_ttl("Team", "frc254") == KEY_EXISTS_CACHE_TTL_DEFAULT

    # Districts: always 24 hours
    assert (
        _get_key_exists_ttl("District", f"{current_year}fim")
        == KEY_EXISTS_CACHE_TTL_DEFAULT
    )
    assert _get_key_exists_ttl("District", "2014mar") == KEY_EXISTS_CACHE_TTL_DEFAULT

    # Past events & matches: 24 hours
    assert _get_key_exists_ttl("Event", "2020casj") == KEY_EXISTS_CACHE_TTL_DEFAULT
    assert _get_key_exists_ttl("Match", "2020casj_qm1") == KEY_EXISTS_CACHE_TTL_DEFAULT

    # Current year events & matches: 1 hour
    assert (
        _get_key_exists_ttl("Event", f"{current_year}casj")
        == KEY_EXISTS_CACHE_TTL_CURRENT_YEAR
    )
    assert (
        _get_key_exists_ttl("Match", f"{current_year}casj_qm1")
        == KEY_EXISTS_CACHE_TTL_CURRENT_YEAR
    )


def test_validate_keys_differentiated_ttl_applied(ndb_stub, api_client: Client) -> None:
    current_year = datetime.date.today().year

    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    Team(id="frc254", team_number=254).put()
    Event(
        id="2020casj",
        year=2020,
        event_short="casj",
        event_type_enum=EventType.REGIONAL,
    ).put()
    Event(
        id=f"{current_year}casj",
        year=current_year,
        event_short="casj",
        event_type_enum=EventType.REGIONAL,
    ).put()
    Match(
        id=f"{current_year}casj_qm1",
        year=current_year,
        event=ndb.Key(Event, f"{current_year}casj"),
        alliances_json="",
        comp_level="qm",
        match_number=1,
        set_number=1,
    ).put()

    # 1. Team: 24-hour TTL
    api_client.get("/api/v3/team/frc254", headers={"X-TBA-Auth-Key": "test_auth_key"})
    team_entry = key_exists_cache._cache.get(("Team", "frc254"))
    assert team_entry is not None
    team_ttl = team_entry.expires_at - time.monotonic()
    assert team_ttl > 80000

    # 2. Historical Event: 24-hour TTL
    api_client.get(
        "/api/v3/event/2020casj", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    hist_event_entry = key_exists_cache._cache.get(("Event", "2020casj"))
    assert hist_event_entry is not None
    hist_event_ttl = hist_event_entry.expires_at - time.monotonic()
    assert hist_event_ttl > 80000

    # 3. Current year Event: 1-hour TTL
    api_client.get(
        f"/api/v3/event/{current_year}casj",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    curr_event_entry = key_exists_cache._cache.get(("Event", f"{current_year}casj"))
    assert curr_event_entry is not None
    curr_event_ttl = curr_event_entry.expires_at - time.monotonic()
    assert 3500 < curr_event_ttl <= 3600

    # 4. Current year Match: 1-hour TTL
    api_client.get(
        f"/api/v3/match/{current_year}casj_qm1",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    curr_match_entry = key_exists_cache._cache.get(("Match", f"{current_year}casj_qm1"))
    assert curr_match_entry is not None
    curr_match_ttl = curr_match_entry.expires_at - time.monotonic()
    assert 3500 < curr_match_ttl <= 3600


def test_validate_keys_district_caching(ndb_stub, api_client: Client) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    District(
        id="2014mar",
        year=2014,
        abbreviation="mar",
    ).put()

    # 1. Existing district key is cached in positive cache
    resp1 = api_client.get(
        "/api/v3/district/2014mar/events", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp1.status_code == 200
    assert key_exists_cache.get(("District", "2014mar")) is True

    # 2. Non-existent district key is cached in negative cache
    resp2 = api_client.get(
        "/api/v3/district/2014nonexistent/events",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp2.status_code == 404
    assert key_does_not_exist_cache.get(("District", "2014nonexistent")) is True


def test_validate_keys_event_code_exception_cross_caching(ndb_stub) -> None:
    Event(
        id="2020arc",
        year=2020,
        event_short="arc",
        event_type_enum=EventType.CMP_DIVISION,
    ).put()

    @validate_keys
    def handler(event_key: str):
        return "success"

    # Positive cross-caching: 2020archimedes resolves to 2020arc
    res = handler(event_key="2020archimedes")
    assert res == "success"
    assert key_exists_cache.get(("Event", "2020archimedes")) is True
    assert key_exists_cache.get(("Event", "2020arc")) is True

    # Negative cross-caching: 2019archimedes resolves to 2019arc, neither exists
    err_resp, status = handler(event_key="2019archimedes")
    assert status == 404
    assert key_does_not_exist_cache.get(("Event", "2019archimedes")) is True
    assert key_does_not_exist_cache.get(("Event", "2019arc")) is True


def test_validate_keys_hot_path_bypasses_negative_cache(
    ndb_stub, api_client: Client
) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    Team(id="frc254", team_number=254).put()

    # 1. First request warms the positive cache
    resp1 = api_client.get(
        "/api/v3/team/frc254", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp1.status_code == 200

    # 2. Second request should hit key_exists_cache directly without checking key_does_not_exist_cache
    mock_get = MagicMock(side_effect=key_does_not_exist_cache.get)
    with patch.object(key_does_not_exist_cache, "get", mock_get):
        resp2 = api_client.get(
            "/api/v3/team/frc254", headers={"X-TBA-Auth-Key": "test_auth_key"}
        )
        assert resp2.status_code == 200
        mock_get.assert_not_called()
