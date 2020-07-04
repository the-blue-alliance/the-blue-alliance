from freezegun import freeze_time
from google.cloud import ndb
from werkzeug.test import Client

from backend.web.handlers.tests import helpers


def test_et_bad_team_num(web_client: Client) -> None:
    resp = web_client.get("/team/0")
    assert resp.status_code == 404


def test_team_not_found(web_client: Client) -> None:
    resp = web_client.get("/team/254")
    assert resp.status_code == 404


def test_team_found_no_events(web_client: Client, ndb_client: ndb.Client) -> None:
    helpers.preseed_team(ndb_client, 254)
    resp = web_client.get("/team/254")
    # This should render team history, but it's not implemented yet
    assert resp.status_code == 200
    assert (
        helpers.get_page_title(resp.data)
        == "The 254 Team - Team 254 (History) - The Blue Alliance"
    )


@freeze_time("2020-02-01")
def test_page_title(web_client: Client, ndb_client: ndb.Client) -> None:
    helpers.preseed_team(ndb_client, 254)
    # We need an event to not render the history page
    helpers.preseed_event_for_team(ndb_client, 254, "2020test")
    resp = web_client.get("/team/254")
    assert resp.status_code == 200
    assert (
        helpers.get_page_title(resp.data)
        == "The 254 Team - Team 254 - The Blue Alliance"
    )


@freeze_time("2020-02-01")
def test_team_info(web_client: Client, ndb_client: ndb.Client) -> None:
    helpers.preseed_team(ndb_client, 254)
    # We need an event to not render the history page
    helpers.preseed_event_for_team(ndb_client, 254, "2020test")
    resp = web_client.get("/team/254")
    assert resp.status_code == 200

    team_info = helpers.get_team_info(resp.data)
    assert team_info.header == "Team 254 - The 254 Team"
    assert team_info.location == "New York, NY, USA"
    assert team_info.full_name == "The Blue Alliance / Some High School"
    assert team_info.rookie_year == "Rookie Year: 2008"
