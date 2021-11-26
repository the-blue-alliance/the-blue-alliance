from google.appengine.ext import ndb
from werkzeug.test import Client

from backend.api.handlers.helpers.model_properties import simple_team_properties
from backend.common.consts.auth_type import AuthType
from backend.common.models.api_auth_access import ApiAuthAccess
from backend.common.models.event_team import EventTeam
from backend.common.models.team import Team


def validate_nominal_keys(team):
    assert set(team.keys()).difference(set(simple_team_properties)) != set()


def validate_simple_keys(team):
    assert set(team.keys()).difference(set(simple_team_properties)) == set()


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
    validate_nominal_keys(resp.json)

    # Simple response
    resp = api_client.get(
        "/api/v3/team/frc254/simple", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert resp.json["key"] == "frc254"
    validate_simple_keys(resp.json)

    # Keys response
    resp = api_client.get(
        "/api/v3/team/frc254/keys", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 404


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
        validate_nominal_keys(team)
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
        validate_simple_keys(team)
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
        validate_nominal_keys(team)
    assert resp.json[0]["key"] == "frc67"
    assert resp.json[1]["key"] == "frc254"

    resp = api_client.get(
        "/api/v3/teams/1", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 1
    for team in resp.json:
        validate_nominal_keys(team)
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
        validate_simple_keys(team)
    assert resp.json[0]["key"] == "frc67"
    assert resp.json[1]["key"] == "frc254"

    resp = api_client.get(
        "/api/v3/teams/1/simple", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 1
    for team in resp.json:
        validate_simple_keys(team)
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
        validate_nominal_keys(team)
    assert resp.json[0]["key"] == "frc67"

    resp = api_client.get(
        "/api/v3/teams/2019/0", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 1
    for team in resp.json:
        validate_nominal_keys(team)
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
        validate_simple_keys(team)
    assert resp.json[0]["key"] == "frc67"

    resp = api_client.get(
        "/api/v3/teams/2019/0/simple", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == 1
    for team in resp.json:
        validate_simple_keys(team)
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
