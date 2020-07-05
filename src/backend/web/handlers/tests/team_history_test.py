from google.cloud import ndb
from werkzeug.test import Client

from backend.web.handlers.tests import helpers


def test_get_bad_team_num(web_client: Client) -> None:
    resp = web_client.get("/team/0/history")
    assert resp.status_code == 404


def test_team_not_found(web_client: Client) -> None:
    resp = web_client.get("/team/254/history")
    assert resp.status_code == 404


def test_page_title(web_client: Client, ndb_client: ndb.Client) -> None:
    helpers.preseed_team(ndb_client, 254)
    helpers.preseed_event_for_team(ndb_client, 254, "2020test")
    resp = web_client.get("/team/254/history")
    assert resp.status_code == 200
    assert (
        helpers.get_page_title(resp.data)
        == "The 254 Team - Team 254 (History) - The Blue Alliance"
    )


def test_team_info(web_client: Client, setup_full_team) -> None:
    resp = web_client.get("/team/148/history")
    assert resp.status_code == 200

    team_info = helpers.get_team_info(resp.data)
    assert team_info.header == "Team 148 - Robowranglers"
    assert team_info.location == "Greenville, Texas, USA"
    assert (
        team_info.full_name
        == "Innovation First International/L3 Harris&Greenville High School"
    )
    assert team_info.rookie_year == "Rookie Year: 1992"
    assert team_info.website == "http://www.robowranglers148.com/"
    assert team_info.district is None
    assert team_info.district_link is None
    assert team_info.social_media == [
        ("facebook-profile", "robotics-team-148-robowranglers-144761815581405"),
        ("youtube-channel", "robowranglers"),
        ("twitter-profile", "robowranglers"),
        ("github-profile", "team148"),
    ]
    assert team_info.preferred_medias is None
    assert team_info.current_event is None


def test_team_history_table(web_client: Client, setup_full_team) -> None:
    resp = web_client.get("/team/148/history")
    assert resp.status_code == 200

    team_history = helpers.get_team_history(resp.data)
    assert team_history == [
        helpers.TeamEventHistory(year=2019, event="The Remix", awards=[]),
        helpers.TeamEventHistory(
            year=2019, event="Texas Robotics Invitational", awards=[]
        ),
        helpers.TeamEventHistory(
            year=2019, event="Einstein Field (Houston)", awards=[]
        ),
        helpers.TeamEventHistory(
            year=2019,
            event="Roebling Division",
            awards=[
                "Championship Subdivision Winner",
                "Quality Award sponsored by Motorola Solutions Foundation",
            ],
        ),
        helpers.TeamEventHistory(
            year=2019,
            event="FIRST In Texas District Championship",
            awards=["District Championship Winner"],
        ),
        helpers.TeamEventHistory(
            year=2019,
            event="FIT District Dallas Event",
            awards=[
                "District Event Winner",
                "Industrial Design Award sponsored by General Motors",
            ],
        ),
        helpers.TeamEventHistory(
            year=2019,
            event="FIT District Amarillo Event",
            awards=[
                "District Event Winner",
                "Quality Award sponsored by Motorola Solutions Foundation",
            ],
        ),
    ]
