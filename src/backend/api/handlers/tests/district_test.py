import pytest

from google.appengine.ext import ndb
from werkzeug.test import Client

from backend.api.handlers.tests.helpers import (
    validate_nominal_event_keys,
    validate_nominal_team_keys,
    validate_simple_event_keys,
    validate_simple_team_keys,
)
from backend.common.consts.auth_type import AuthType
from backend.common.consts.award_type import AwardType
from backend.common.consts.event_type import EventType
from backend.common.models.api_auth_access import ApiAuthAccess
from backend.common.models.award import Award
from backend.common.models.district import District
from backend.common.models.district_ranking import DistrictRanking
from backend.common.models.district_team import DistrictTeam
from backend.common.models.event import Event
from backend.common.models.team import Team


def test_district_events(ndb_stub, api_client: Client) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    District(
        id="2019fim",
        year=2019,
        abbreviation="fim",
        display_name="Michigan",
    ).put()
    District(
        id="2020fim",
        year=2020,
        abbreviation="fim",
        display_name="Michigan",
    ).put()
    District(
        id="2014mar",
        year=2014,
        abbreviation="mar",
        display_name="Mid-Atlantic",
    ).put()
    District(
        id="2024fma",
        year=2024,
        abbreviation="fma",
        display_name="Mid-Atlantic",
    ).put()
    Event(
        id="2019casj",
        year=2019,
        event_short="casj",
        event_type_enum=EventType.REGIONAL,
        district_key=ndb.Key(District, "2019fim"),
    ).put()
    Event(
        id="2020casj",
        year=2020,
        event_short="casj",
        event_type_enum=EventType.REGIONAL,
        district_key=ndb.Key(District, "2020fim"),
    ).put()
    Event(
        id="2020casf",
        year=2020,
        event_short="casf",
        event_type_enum=EventType.REGIONAL,
        district_key=ndb.Key(District, "2020fim"),
    ).put()

    # Nominal response
    resp = api_client.get(
        "/api/v3/district/2019fim/events", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 1
    for event in resp.json:
        validate_nominal_event_keys(event)
    assert resp.json[0]["key"] == "2019casj"

    resp = api_client.get(
        "/api/v3/district/2020fim/events", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 2
    for event in resp.json:
        validate_nominal_event_keys(event)
    keys = set([event["key"] for event in resp.json])
    assert "2020casf" in keys
    assert "2020casj" in keys

    # Simple response
    resp = api_client.get(
        "/api/v3/district/2019fim/events/simple",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 200
    assert len(resp.json) == 1
    for event in resp.json:
        validate_simple_event_keys(event)
    assert resp.json[0]["key"] == "2019casj"

    resp = api_client.get(
        "/api/v3/district/2020fim/events/simple",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 200
    assert len(resp.json) == 2
    for event in resp.json:
        validate_simple_event_keys(event)
    keys = set([event["key"] for event in resp.json])
    assert "2020casf" in keys
    assert "2020casj" in keys

    # Keys response
    resp = api_client.get(
        "/api/v3/district/2019fim/events/keys",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 200
    assert len(resp.json) == 1
    assert "2019casj" in resp.json

    resp = api_client.get(
        "/api/v3/district/2020fim/events/keys",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 200
    assert len(resp.json) == 2
    assert "2020casf" in resp.json
    assert "2020casj" in resp.json

    resp = api_client.get(
        "/api/v3/district/fim/history",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 200
    assert len(resp.json) == 2
    assert resp.json == [
        {
            "abbreviation": "fim",
            "display_name": "Michigan",
            "key": "2019fim",
            "year": 2019,
        },
        {
            "abbreviation": "fim",
            "display_name": "Michigan",
            "key": "2020fim",
            "year": 2020,
        },
    ]

    resp = api_client.get(
        "/api/v3/district/notadistrict/history",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 200
    assert resp.json == []

    resp = api_client.get(
        "/api/v3/district/fma/history",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 200
    assert len(resp.json) == 2
    assert resp.json == [
        {
            "abbreviation": "mar",
            "display_name": "Mid-Atlantic",
            "key": "2014mar",
            "year": 2014,
        },
        {
            "abbreviation": "fma",
            "display_name": "Mid-Atlantic",
            "key": "2024fma",
            "year": 2024,
        },
    ]

    resp = api_client.get(
        "/api/v3/district/mar/history",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 200
    assert len(resp.json) == 2
    assert resp.json == [
        {
            "abbreviation": "mar",
            "display_name": "Mid-Atlantic",
            "key": "2014mar",
            "year": 2014,
        },
        {
            "abbreviation": "fma",
            "display_name": "Mid-Atlantic",
            "key": "2024fma",
            "year": 2024,
        },
    ]


def test_district_teams(ndb_stub, api_client: Client) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    District(
        id="2019fim",
        year=2019,
        abbreviation="fim",
    ).put()
    Team(id="frc254", team_number=254).put()
    Team(id="frc604", team_number=604).put()
    DistrictTeam(
        id="2019fim_frc254",
        district_key=ndb.Key(District, "2019fim"),
        team=ndb.Key("Team", "frc254"),
        year=2019,
    ).put()
    DistrictTeam(
        id="2019fim_frc604",
        district_key=ndb.Key(District, "2019fim"),
        team=ndb.Key("Team", "frc604"),
        year=2019,
    ).put()

    # Nominal response
    resp = api_client.get(
        "/api/v3/district/2019fim/teams", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 2
    for team in resp.json:
        validate_nominal_team_keys(team)
    keys = set([team["key"] for team in resp.json])
    assert "frc254" in keys
    assert "frc604" in keys

    # Simple response
    resp = api_client.get(
        "/api/v3/district/2019fim/teams/simple",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 200
    assert len(resp.json) == 2
    for team in resp.json:
        validate_simple_team_keys(team)
    keys = set([team["key"] for team in resp.json])
    assert "frc254" in keys
    assert "frc604" in keys

    # Keys response
    resp = api_client.get(
        "/api/v3/district/2019fim/teams/keys",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert len(resp.json) == 2
    assert "frc254" in keys
    assert "frc604" in keys


def test_district_rankings(ndb_stub, api_client: Client) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    District(
        id="2020ne",
        year=2020,
        abbreviation="ne",
    ).put()
    rankings = [
        DistrictRanking(
            rank=13,
            team_key="frc604",
            point_total=50,
            rookie_bonus=5,
            event_points=[],
        )
    ]
    District(
        id="2020fim",
        year=2020,
        abbreviation="fim",
        rankings=rankings,
    ).put()

    # Test empty rankings
    resp = api_client.get(
        "/api/v3/district/2020ne/rankings", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert resp.json is None

    # Test non-empty rankings
    resp = api_client.get(
        "/api/v3/district/2020fim/rankings", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert resp.json == rankings


def test_district_list_year(ndb_stub, api_client: Client) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    District(
        id="2020ne",
        year=2020,
        abbreviation="ne",
    ).put()
    District(
        id="2020fim",
        year=2020,
        abbreviation="fim",
    ).put()

    # Test empty year
    resp = api_client.get(
        "/api/v3/districts/2019", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert resp.json == []

    # Test non-empty year
    resp = api_client.get(
        "/api/v3/districts/2020", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 2
    district_keys = set([d["key"] for d in resp.json])
    assert "2020ne" in district_keys
    assert "2020fim" in district_keys


def test_district_awards(ndb_stub, api_client: Client) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()

    District(
        id="2024ne",
        year=2024,
        abbreviation="ne",
    ).put()

    Team(
        id="frc2713",
        team_number=2713,
    ).put()

    Event(
        id="2024necmp",
        year=2024,
        event_short="necmp",
        district_key=ndb.Key(District, "2024ne"),
        event_type_enum=EventType.DISTRICT_CMP,
    ).put()

    Award(
        id="2024necmp_1",
        name_str="Winner",
        event=ndb.Key(Event, "2024necmp"),
        award_type_enum=AwardType.WINNER,
        event_type_enum=EventType.DISTRICT_CMP,
        year=2024,
        team_list=[ndb.Key(Team, "frc2713")],
    ).put()

    resp = api_client.get(
        "/api/v3/district/2024ne/awards",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )

    assert resp.status_code == 200
    assert len(resp.json) == 1
    assert resp.json == [
        {
            "award_type": AwardType.WINNER,
            "event_key": "2024necmp",
            "name": "Winner",
            "recipient_list": [],
            "year": 2024,
        }
    ]


@pytest.mark.parametrize(
    "endpoint", ["advancement", "awards", "rankings", "teams", "events"]
)
def test_district_endpoints_validate(endpoint, ndb_stub, api_client: Client) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()

    # Invalid district endpoint
    resp = api_client.get(
        f"/api/v3/district/2024Minnesota/{endpoint}",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 404
    assert resp.json == {"Error": "2024Minnesota is not a valid district key"}

    # Missing district
    resp = api_client.get(
        f"/api/v3/district/2024ne/{endpoint}",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 404
    assert resp.json == {"Error": "district key: 2024ne does not exist"}

    District(
        id="2024ne",
        year=2024,
        abbreviation="ne",
    ).put()

    resp = api_client.get(
        f"/api/v3/district/2024ne/{endpoint}",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 200
