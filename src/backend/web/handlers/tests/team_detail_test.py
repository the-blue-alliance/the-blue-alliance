from freezegun import freeze_time
from google.cloud import ndb
from werkzeug.test import Client

from backend.web.handlers.tests import helpers


def test_get_bad_team_num(web_client: Client) -> None:
    resp = web_client.get("/team/0/2020")
    assert resp.status_code == 404


def test_team_not_found(web_client: Client) -> None:
    resp = web_client.get("/team/254/2020")
    assert resp.status_code == 404


def test_team_found_no_events(web_client: Client, ndb_client: ndb.Client) -> None:
    helpers.preseed_team(ndb_client, 254)
    resp = web_client.get("/team/254/2020")
    assert resp.status_code == 404


def test_page_title(web_client: Client, ndb_client: ndb.Client) -> None:
    helpers.preseed_team(ndb_client, 254)
    helpers.preseed_event_for_team(ndb_client, 254, "2020test")
    resp = web_client.get("/team/254/2020")
    assert resp.status_code == 200
    assert (
        helpers.get_page_title(resp.data)
        == "The 254 Team - Team 254 (2020) - The Blue Alliance"
    )


def test_team_info(web_client: Client, setup_full_team) -> None:
    resp = web_client.get("/team/148/2019")
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
    assert team_info.district == "FIRST In Texas District"
    assert team_info.district_link == "/events/tx/2019"
    assert team_info.social_media == [
        ("facebook-profile", "robotics-team-148-robowranglers-144761815581405"),
        ("youtube-channel", "robowranglers"),
        ("twitter-profile", "robowranglers"),
        ("github-profile", "team148"),
    ]
    assert team_info.preferred_medias == [
        ("imgur", "1FqA6wa"),
    ]
    assert team_info.current_event is None


@freeze_time("2019-03-30")  # This makes 2019txdls active
def test_team_info_live_event_no_upcoming_matches(
    web_client: Client, setup_full_team
) -> None:
    resp = web_client.get("/team/148/2019")
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
    assert team_info.district == "FIRST In Texas District"
    assert team_info.district_link == "/events/tx/2019"
    assert team_info.social_media == [
        ("facebook-profile", "robotics-team-148-robowranglers-144761815581405"),
        ("youtube-channel", "robowranglers"),
        ("twitter-profile", "robowranglers"),
        ("github-profile", "team148"),
    ]
    # If there's a live event, don't show the preferred media
    assert team_info.preferred_medias is None
    assert team_info.current_event == helpers.TeamCurrentEvent(
        event_key="2019txdls",
        webcast=("/gameday/2019txdls", "Watch Now"),
        currently_competing="Currently competing at:FIT District Dallas Event",
        upcoming_matches=False,
    )


def test_team_year_dropdown(web_client: Client, ndb_client: ndb.Client) -> None:
    helpers.preseed_team(ndb_client, 254)
    # Use out-of-order years here to make sure they're sorted properly
    [
        helpers.preseed_event_for_team(ndb_client, 254, f"{year}test")
        for year in [2019, 2020, 2018]
    ]

    resp = web_client.get("/team/254/2020")
    assert resp.status_code == 200
    dropdown_years = helpers.get_years_participated_dropdown(resp.data)
    assert dropdown_years == ["History", "2020 Season", "2019 Season", "2018 Season"]


def test_team_participation_event_details(
    web_client: Client, ndb_client: ndb.Client
) -> None:
    helpers.preseed_team(ndb_client, 254)
    helpers.preseed_event_for_team(ndb_client, 254, "2020test")

    resp = web_client.get("/team/254/2020")
    assert resp.status_code == 200
    event_info = helpers.get_team_event_participation(resp.data, "2020test")
    assert event_info.event_name == "Test Event"
