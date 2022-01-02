from google.appengine.ext import ndb
from werkzeug.test import Client

from backend.api.handlers.tests.helpers import (
    validate_nominal_event_keys,
    validate_nominal_team_keys,
    validate_simple_event_keys,
    validate_simple_team_keys,
)
from backend.common.consts.auth_type import AuthType
from backend.common.consts.event_type import EventType
from backend.common.consts.media_type import MediaType
from backend.common.models.api_auth_access import ApiAuthAccess
from backend.common.models.district import District
from backend.common.models.district_team import DistrictTeam
from backend.common.models.event import Event
from backend.common.models.event_team import EventTeam
from backend.common.models.media import Media
from backend.common.models.robot import Robot
from backend.common.models.team import Team


def test_team(ndb_stub, api_client: Client) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    Team(id="frc254", team_number=254).put()

    # Nominal response
    resp = api_client.get(
        "/api/v3/team/frc254", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert resp.json["key"] == "frc254"
    validate_nominal_team_keys(resp.json)

    # Simple response
    resp = api_client.get(
        "/api/v3/team/frc254/simple", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert resp.json["key"] == "frc254"
    validate_simple_team_keys(resp.json)

    # Keys response
    resp = api_client.get(
        "/api/v3/team/frc254/keys", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 404


def test_team_years_participated(ndb_stub, api_client: Client) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    Team(id="frc254", team_number=254).put()
    EventTeam(
        id="1992casj_frc254",
        event=ndb.Key("Event", "1992casj"),
        team=ndb.Key("Team", "frc254"),
        year=1992,
    ).put()
    EventTeam(
        id="2010casj_frc254",
        event=ndb.Key("Event", "2010casj"),
        team=ndb.Key("Team", "frc254"),
        year=2010,
    ).put()
    EventTeam(
        id="2020casj_frc254",
        event=ndb.Key("Event", "2020casj"),
        team=ndb.Key("Team", "frc254"),
        year=2020,
    ).put()

    resp = api_client.get(
        "/api/v3/team/frc254/years_participated",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 200
    assert resp.json == [1992, 2010, 2020]


def test_team_history_districts(ndb_stub, api_client: Client) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    Team(id="frc254", team_number=254).put()
    District(
        id="2015fim",
        year=2015,
        abbreviation="fim",
    ).put()
    District(
        id="2020fim",
        year=2020,
        abbreviation="fim",
    ).put()
    DistrictTeam(
        id="2015fim_frc254",
        district_key=ndb.Key(District, "2015fim"),
        team=ndb.Key(Team, "frc254"),
        year=2015,
    ).put()
    DistrictTeam(
        id="2020fim_frc254",
        district_key=ndb.Key(District, "2020fim"),
        team=ndb.Key(Team, "frc254"),
        year=2020,
    ).put()

    resp = api_client.get(
        "/api/v3/team/frc254/districts",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 200
    assert len(resp.json) == 2
    district_keys = set([d["key"] for d in resp.json])
    assert "2015fim" in district_keys
    assert "2020fim" in district_keys


def test_team_history_robots(ndb_stub, api_client: Client) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    Team(id="frc254", team_number=254).put()
    Robot(
        id="frc254_2010",
        team=ndb.Key("Team", "frc254"),
        year=2010,
    ).put()
    Robot(
        id="frc254_2020",
        team=ndb.Key("Team", "frc254"),
        year=2020,
    ).put()

    resp = api_client.get(
        "/api/v3/team/frc254/robots",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 200
    assert len(resp.json) == 2
    robot_keys = set([d["key"] for d in resp.json])
    assert "frc254_2010" in robot_keys
    assert "frc254_2020" in robot_keys


def test_team_social_media(ndb_stub, api_client: Client) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    Team(id="frc254", team_number=254).put()
    Media(
        references=[ndb.Key("Team", "frc254")],
        year=None,
        media_type_enum=MediaType.FACEBOOK_PROFILE,
        foreign_key="test",
        details_json="{}",
    ).put()
    Media(
        references=[ndb.Key("Team", "frc254")],
        year=None,
        media_type_enum=MediaType.GITHUB_PROFILE,
        foreign_key="test",
        details_json="{}",
    ).put()

    resp = api_client.get(
        "/api/v3/team/frc254/social_media",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 200
    assert len(resp.json) == 2


def test_team_events(ndb_stub, api_client: Client) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    Team(id="frc254", team_number=254).put()
    Event(
        id="2019casj",
        year=2019,
        event_short="casj",
        event_type_enum=EventType.REGIONAL,
    ).put()
    Event(
        id="2019casf",
        year=2019,
        event_short="casf",
        event_type_enum=EventType.REGIONAL,
    ).put()
    EventTeam(
        id="2019casj_frc254",
        event=ndb.Key("Event", "2019casj"),
        team=ndb.Key("Team", "frc254"),
    ).put()
    EventTeam(
        id="2019casf_frc254",
        event=ndb.Key("Event", "2019casf"),
        team=ndb.Key("Team", "frc254"),
    ).put()

    # Nominal response
    resp = api_client.get(
        "/api/v3/team/frc254/events", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 2
    for event in resp.json:
        validate_nominal_event_keys(event)

    # Simple response
    resp = api_client.get(
        "/api/v3/team/frc254/events/simple", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 2
    for event in resp.json:
        validate_simple_event_keys(event)

    # Keys response
    resp = api_client.get(
        "/api/v3/team/frc254/events/keys", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 2


def test_team_list_all(ndb_stub, api_client: Client) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    Team(id="frc67", team_number=67).put()
    Team(id="frc254", team_number=254).put()
    Team(id="frc604", team_number=604).put()
    Team(id="frc9999", team_number=9999).put()

    # Nominal response
    resp = api_client.get(
        "/api/v3/teams/all", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 4
    for team in resp.json:
        validate_nominal_team_keys(team)
    assert resp.json[0]["key"] == "frc67"
    assert resp.json[1]["key"] == "frc254"
    assert resp.json[2]["key"] == "frc604"
    assert resp.json[3]["key"] == "frc9999"

    # Simple response
    resp = api_client.get(
        "/api/v3/teams/all/simple", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 4
    for team in resp.json:
        validate_simple_team_keys(team)
    assert resp.json[0]["key"] == "frc67"
    assert resp.json[1]["key"] == "frc254"
    assert resp.json[2]["key"] == "frc604"
    assert resp.json[3]["key"] == "frc9999"

    # Keys response
    resp = api_client.get(
        "/api/v3/teams/all/keys", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 4
    assert resp.json[0] == "frc67"
    assert resp.json[1] == "frc254"
    assert resp.json[2] == "frc604"
    assert resp.json[3] == "frc9999"


def test_team_list(ndb_stub, api_client: Client) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    Team(id="frc67", team_number=67).put()
    Team(id="frc254", team_number=254).put()
    Team(id="frc604", team_number=604).put()
    Team(id="frc9999", team_number=9999).put()

    # Nominal response
    resp = api_client.get(
        "/api/v3/teams/0", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 2
    for team in resp.json:
        validate_nominal_team_keys(team)
    assert resp.json[0]["key"] == "frc67"
    assert resp.json[1]["key"] == "frc254"

    resp = api_client.get(
        "/api/v3/teams/1", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 1
    for team in resp.json:
        validate_nominal_team_keys(team)
    assert resp.json[0]["key"] == "frc604"

    resp = api_client.get(
        "/api/v3/teams/2", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 0

    # Simple response
    resp = api_client.get(
        "/api/v3/teams/0/simple", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 2
    for team in resp.json:
        validate_simple_team_keys(team)
    assert resp.json[0]["key"] == "frc67"
    assert resp.json[1]["key"] == "frc254"

    resp = api_client.get(
        "/api/v3/teams/1/simple", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 1
    for team in resp.json:
        validate_simple_team_keys(team)
    assert resp.json[0]["key"] == "frc604"

    resp = api_client.get(
        "/api/v3/teams/2/simple", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 0

    # Keys response
    resp = api_client.get(
        "/api/v3/teams/0/keys", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 2
    assert resp.json[0] == "frc67"
    assert resp.json[1] == "frc254"

    resp = api_client.get(
        "/api/v3/teams/1/keys", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 1
    assert resp.json[0] == "frc604"

    resp = api_client.get(
        "/api/v3/teams/2/keys", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 0


def test_team_list_year(ndb_stub, api_client: Client) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()
    Team(id="frc67", team_number=67).put()
    Team(id="frc254", team_number=254).put()
    EventTeam(
        id="2020casj_frc67",
        event=ndb.Key("Event", "2020casj"),
        team=ndb.Key("Team", "frc67"),
        year=2020,
    ).put()
    EventTeam(
        id="2019casj_frc254",
        event=ndb.Key("Event", "2019casj"),
        team=ndb.Key("Team", "frc254"),
        year=2019,
    ).put()

    # Nominal response
    resp = api_client.get(
        "/api/v3/teams/2020/0", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 1
    for team in resp.json:
        validate_nominal_team_keys(team)
    assert resp.json[0]["key"] == "frc67"

    resp = api_client.get(
        "/api/v3/teams/2019/0", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 1
    for team in resp.json:
        validate_nominal_team_keys(team)
    assert resp.json[0]["key"] == "frc254"

    resp = api_client.get(
        "/api/v3/teams/2018/0", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 0

    # Simple response
    resp = api_client.get(
        "/api/v3/teams/2020/0/simple", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 1
    for team in resp.json:
        validate_simple_team_keys(team)
    assert resp.json[0]["key"] == "frc67"

    resp = api_client.get(
        "/api/v3/teams/2019/0/simple", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 1
    for team in resp.json:
        validate_simple_team_keys(team)
    assert resp.json[0]["key"] == "frc254"

    resp = api_client.get(
        "/api/v3/teams/2018/0/simple", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 0

    # Keys response
    resp = api_client.get(
        "/api/v3/teams/2020/0/keys", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 1
    assert resp.json[0] == "frc67"

    resp = api_client.get(
        "/api/v3/teams/2019/0/keys", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 1
    assert resp.json[0] == "frc254"

    resp = api_client.get(
        "/api/v3/teams/2018/0/keys", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 0
