from werkzeug.test import Client

from backend.common.models.team import Team


def test_team(api_client: Client) -> None:
    Team(id="frc254", team_number=254).put()
    resp = api_client.get("/api/v3/team/frc254", headers={"X-TBA-Auth-Key": "test"})
    assert resp.status_code == 200


def test_team_list(api_client: Client) -> None:
    Team(id="frc254", team_number=254).put()
    resp = api_client.get("/api/v3/teams/0", headers={"X-TBA-Auth-Key": "test"})
    assert resp.status_code == 200
