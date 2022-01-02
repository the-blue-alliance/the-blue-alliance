import json

from google.appengine.ext import ndb
from werkzeug.test import Client

from backend.api.handlers.helpers.add_alliance_status import add_alliance_status
from backend.api.handlers.tests.helpers import (
    validate_nominal_event_keys,
    validate_nominal_match_keys,
    validate_nominal_team_keys,
    validate_simple_event_keys,
    validate_simple_match_keys,
    validate_simple_team_keys,
)
from backend.common.consts.auth_type import AuthType
from backend.common.consts.award_type import AwardType
from backend.common.consts.event_type import EventType
from backend.common.models.alliance import EventAlliance
from backend.common.models.api_auth_access import ApiAuthAccess
from backend.common.models.award import Award
from backend.common.models.event import Event
from backend.common.models.event_details import EventDetails
from backend.common.models.event_district_points import (
    EventDistrictPoints,
    TeamAtEventDistrictPoints,
)
from backend.common.models.event_team import EventTeam
from backend.common.models.match import Match
from backend.common.models.team import Team


def test_event(ndb_stub, api_client: Client) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    Event(
        id="2019casj",
        year=2019,
        event_short="casj",
        event_type_enum=EventType.REGIONAL,
    ).put()

    # Nominal response
    resp = api_client.get(
        "/api/v3/event/2019casj", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert resp.json["key"] == "2019casj"
    validate_nominal_event_keys(resp.json)

    # Simple response
    resp = api_client.get(
        "/api/v3/event/2019casj/simple", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert resp.json["key"] == "2019casj"
    validate_simple_event_keys(resp.json)

    # Keys response
    resp = api_client.get(
        "/api/v3/event/2019casj/keys", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 404


def test_event_list_all(ndb_stub, api_client: Client) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    Event(
        id="2019casj",
        year=2019,
        event_short="casj",
        event_type_enum=EventType.REGIONAL,
    ).put()
    Event(
        id="2020casj",
        year=2020,
        event_short="casj",
        event_type_enum=EventType.REGIONAL,
    ).put()

    # Nominal response
    resp = api_client.get(
        "/api/v3/events/all", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 2
    for event in resp.json:
        validate_nominal_event_keys(event)
    keys = set([event["key"] for event in resp.json])
    assert "2019casj" in keys
    assert "2020casj" in keys

    # Simple response
    resp = api_client.get(
        "/api/v3/events/all/simple", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 2
    for event in resp.json:
        validate_simple_event_keys(event)
    keys = set([event["key"] for event in resp.json])
    assert "2019casj" in keys
    assert "2020casj" in keys

    # Keys response
    resp = api_client.get(
        "/api/v3/events/all/keys", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert len(resp.json) == 2
    assert "2019casj" in resp.json
    assert "2020casj" in resp.json


def test_event_list_year(ndb_stub, api_client: Client) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    Event(
        id="2019casj",
        year=2019,
        event_short="casj",
        event_type_enum=EventType.REGIONAL,
    ).put()
    Event(
        id="2020casj",
        year=2020,
        event_short="casj",
        event_type_enum=EventType.REGIONAL,
    ).put()
    Event(
        id="2020casf",
        year=2020,
        event_short="casf",
        event_type_enum=EventType.REGIONAL,
    ).put()

    # Nominal response
    resp = api_client.get(
        "/api/v3/events/2019", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 1
    for event in resp.json:
        validate_nominal_event_keys(event)
    assert resp.json[0]["key"] == "2019casj"

    resp = api_client.get(
        "/api/v3/events/2020", headers={"X-TBA-Auth-Key": "test_auth_key"}
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
        "/api/v3/events/2019/simple", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 1
    for event in resp.json:
        validate_simple_event_keys(event)
    assert resp.json[0]["key"] == "2019casj"

    resp = api_client.get(
        "/api/v3/events/2020/simple", headers={"X-TBA-Auth-Key": "test_auth_key"}
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
        "/api/v3/events/2019/keys", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 1
    assert "2019casj" in resp.json

    resp = api_client.get(
        "/api/v3/events/2020/keys", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 2
    assert "2020casf" in resp.json
    assert "2020casj" in resp.json


def test_event_details(ndb_stub, api_client: Client) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    Event(
        id="2019casj",
        year=2019,
        event_short="casj",
        event_type_enum=EventType.REGIONAL,
    ).put()
    alliances = [
        EventAlliance(picks=["frc1", "frc2", "frc3"]),
        EventAlliance(picks=["frc4", "frc5", "frc6"]),
        EventAlliance(picks=["frc7", "frc8", "frc9"]),
        EventAlliance(picks=["frc10", "frc11", "frc12"]),
    ]
    district_points = EventDistrictPoints(
        points={
            "frc254": TeamAtEventDistrictPoints(
                event_key="2019casj",
                qual_points=10,
                elim_points=20,
                alliance_points=10,
                award_points=5,
                total=45,
            )
        },
        tiebreakers={},
    )
    EventDetails(
        id="2019casj",
        alliance_selections=alliances,
        district_points=district_points,
    ).put()

    # Alliances response
    alliances_resp = api_client.get(
        "/api/v3/event/2019casj/alliances", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert alliances_resp.status_code == 200
    add_alliance_status("2019casj", alliances)
    assert alliances_resp.json == alliances

    # District points response
    district_points_resp = api_client.get(
        "/api/v3/event/2019casj/district_points",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert district_points_resp.status_code == 200
    assert district_points_resp.json == district_points


def test_event_teams(ndb_stub, api_client: Client) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    Event(
        id="2019casj",
        year=2019,
        event_short="casj",
        event_type_enum=EventType.REGIONAL,
    ).put()
    Team(id="frc254", team_number=254).put()
    Team(id="frc604", team_number=604).put()
    EventTeam(
        id="2019casj_frc254",
        event=ndb.Key("Event", "2019casj"),
        team=ndb.Key("Team", "frc254"),
    ).put()
    EventTeam(
        id="2019casj_frc604",
        event=ndb.Key("Event", "2019casj"),
        team=ndb.Key("Team", "frc604"),
    ).put()

    # Nominal response
    resp = api_client.get(
        "/api/v3/event/2019casj/teams", headers={"X-TBA-Auth-Key": "test_auth_key"}
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
        "/api/v3/event/2019casj/teams/simple",
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
        "/api/v3/event/2019casj/teams/keys", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert len(resp.json) == 2
    assert "frc254" in keys
    assert "frc604" in keys


def test_event_matches(ndb_stub, api_client: Client) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    Event(
        id="2019casj",
        year=2019,
        event_short="casj",
        event_type_enum=EventType.REGIONAL,
    ).put()
    Match(
        id="2019casj_qm1",
        comp_level="qm",
        match_number=1,
        year=2019,
        set_number=1,
        event=ndb.Key("Event", "2019casj"),
        alliances_json=json.dumps(
            {
                "red": {"score": 0, "teams": []},
                "blue": {"score": 0, "teams": []},
            }
        ),
    ).put()
    Match(
        id="2019casj_qm2",
        comp_level="qm",
        match_number=2,
        year=2019,
        set_number=1,
        event=ndb.Key("Event", "2019casj"),
        alliances_json=json.dumps(
            {
                "red": {"score": 0, "teams": []},
                "blue": {"score": 0, "teams": []},
            }
        ),
    ).put()

    # Nominal response
    resp = api_client.get(
        "/api/v3/event/2019casj/matches", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 2
    for match in resp.json:
        validate_nominal_match_keys(match)
    keys = set([match["key"] for match in resp.json])
    assert "2019casj_qm1" in keys
    assert "2019casj_qm2" in keys

    # Simple response
    resp = api_client.get(
        "/api/v3/event/2019casj/matches/simple",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 200
    assert len(resp.json) == 2
    for match in resp.json:
        validate_simple_match_keys(match)
    keys = set([match["key"] for match in resp.json])
    assert "2019casj_qm1" in keys
    assert "2019casj_qm2" in keys

    # Keys response
    resp = api_client.get(
        "/api/v3/event/2019casj/matches/keys",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert len(resp.json) == 2
    assert "2019casj_qm1" in keys
    assert "2019casj_qm2" in keys


def test_event_awards(ndb_stub, api_client: Client) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    Event(
        id="2019casj",
        year=2019,
        event_short="casj",
        event_type_enum=EventType.REGIONAL,
    ).put()
    Award(
        id="2019casj_1",
        year=2019,
        award_type_enum=AwardType.WINNER,
        event_type_enum=EventType.REGIONAL,
        event=ndb.Key(Event, "2019casj"),
        name_str="Winner",
    ).put()
    Award(
        id="2019casj_2",
        year=2019,
        award_type_enum=AwardType.FINALIST,
        event_type_enum=EventType.REGIONAL,
        event=ndb.Key(Event, "2019casj"),
        name_str="Finalist",
    ).put()

    # Nominal response
    resp = api_client.get(
        "/api/v3/event/2019casj/awards", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 2
    names = set([award["name"] for award in resp.json])
    assert "Winner" in names
    assert "Finalist" in names
