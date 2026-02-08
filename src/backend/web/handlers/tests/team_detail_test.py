import json

from bs4 import BeautifulSoup
from freezegun import freeze_time
from werkzeug.test import Client

from backend.common.consts.webcast_status import WebcastStatus
from backend.common.consts.webcast_type import WebcastType
from backend.common.memcache_models.webcast_online_status_memcache import (
    WebcastOnlineStatusMemcache,
)
from backend.common.models.webcast import Webcast
from backend.web.handlers.tests import helpers


def test_get_bad_team_num(web_client: Client) -> None:
    resp = web_client.get("/team/0/2020")
    assert resp.status_code == 404


def test_get_bad_year(web_client: Client, ndb_stub) -> None:
    helpers.preseed_team(254)
    resp = web_client.get("/team/254/1337")
    assert resp.status_code == 404


def test_team_not_found(web_client: Client) -> None:
    resp = web_client.get("/team/254/2020")
    assert resp.status_code == 404


def test_team_found_no_events(web_client: Client, ndb_stub) -> None:
    helpers.preseed_team(254)
    resp = web_client.get("/team/254/2020")
    assert resp.status_code == 404


def test_page_title(web_client: Client, ndb_stub) -> None:
    helpers.preseed_team(254)
    helpers.preseed_event_for_team(254, "2020test")
    resp = web_client.get("/team/254/2020")
    assert resp.status_code == 200
    assert "max-age=21600" in resp.headers["Cache-Control"]
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
    # Removed team website
    # assert team_info.website == "http://www.robowranglers148.com/"
    assert team_info.website is None
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
    webcast_status = Webcast(
        type=WebcastType.TWITCH,
        channel="firstintexasevents",
        status=WebcastStatus.ONLINE,
        stream_title="Live Stream",
        viewer_count=100,
    )
    WebcastOnlineStatusMemcache(webcast_status).put(webcast_status)

    resp = web_client.get("/team/148/2019")
    assert resp.status_code == 200
    assert "max-age=61" in resp.headers["Cache-Control"]

    team_info = helpers.get_team_info(resp.data)
    assert team_info.header == "Team 148 - Robowranglers"
    assert team_info.location == "Greenville, Texas, USA"
    assert (
        team_info.full_name
        == "Innovation First International/L3 Harris&Greenville High School"
    )
    assert team_info.rookie_year == "Rookie Year: 1992"
    # Removed website
    # assert team_info.website == "http://www.robowranglers148.com/"
    assert team_info.website is None
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


def test_team_year_dropdown(web_client: Client, ndb_stub) -> None:
    helpers.preseed_team(254)
    # Use out-of-order years here to make sure they're sorted properly
    [helpers.preseed_event_for_team(254, f"{year}test") for year in [2019, 2020, 2018]]

    resp = web_client.get("/team/254/2020")
    assert resp.status_code == 200
    dropdown_years = helpers.get_years_participated_dropdown(resp.data)
    assert dropdown_years == ["History", "2020 Season", "2019 Season", "2018 Season"]


def test_team_participation_event_details(web_client: Client, ndb_stub) -> None:
    helpers.preseed_team(254)
    helpers.preseed_event_for_team(254, "2020test")

    resp = web_client.get("/team/254/2020")
    assert resp.status_code == 200
    event_info = helpers.get_team_event_participation(resp.data, "2020test")
    assert event_info.event_name == "Test Event"


def test_schema_org_sports_team(web_client: Client, ndb_stub) -> None:
    """Test that team pages include schema.org SportsTeam JSON-LD markup."""
    helpers.preseed_team(254)
    helpers.preseed_event_for_team(254, "2020test")

    resp = web_client.get("/team/254/2020")
    assert resp.status_code == 200

    soup = BeautifulSoup(resp.data, "html.parser")

    # Find the JSON-LD script tag
    schema_scripts = soup.find_all("script", {"type": "application/ld+json"})
    assert len(schema_scripts) >= 1

    # Find the SportsTeam schema
    sports_team_schema = None
    for script in schema_scripts:
        data = json.loads(script.string)
        if data.get("@type") == "SportsTeam":
            sports_team_schema = data
            break

    assert sports_team_schema is not None
    assert sports_team_schema["@context"] == "https://schema.org"
    assert sports_team_schema["@type"] == "SportsTeam"
    assert sports_team_schema["@id"] == "https://www.thebluealliance.com/team/254"
    assert sports_team_schema["name"] == "The 254 Team"
    assert sports_team_schema["alternateName"] == "FRC Team 254"
    assert sports_team_schema["sport"] == "Robotics"
    assert sports_team_schema["foundingDate"] == "2008"

    # Check location
    assert "location" in sports_team_schema
    assert sports_team_schema["location"]["@type"] == "Place"
    assert sports_team_schema["location"]["address"]["@type"] == "PostalAddress"
    assert sports_team_schema["location"]["address"]["addressLocality"] == "New York"
    assert sports_team_schema["location"]["address"]["addressRegion"] == "NY"
    assert sports_team_schema["location"]["address"]["addressCountry"] == "USA"

    # Check memberOf
    assert sports_team_schema["memberOf"]["@type"] == "SportsOrganization"
    assert sports_team_schema["memberOf"]["name"] == "FIRST"
    assert sports_team_schema["memberOf"]["url"] == "https://www.firstinspires.org"

    # Check sameAs
    assert (
        "https://frc-events.firstinspires.org/team/254" in sports_team_schema["sameAs"]
    )

    # Check website
    assert sports_team_schema["url"] == "https://www.thebluealliance.com"


def test_schema_org_sports_team_full_data(web_client: Client, setup_full_team) -> None:
    """Test schema.org markup with full team data."""
    resp = web_client.get("/team/148/2019")
    assert resp.status_code == 200

    soup = BeautifulSoup(resp.data, "html.parser")

    # Find the SportsTeam schema
    schema_scripts = soup.find_all("script", {"type": "application/ld+json"})
    sports_team_schema = None
    for script in schema_scripts:
        data = json.loads(script.string)
        if data.get("@type") == "SportsTeam":
            sports_team_schema = data
            break

    assert sports_team_schema is not None
    assert sports_team_schema["name"] == "Robowranglers"
    assert sports_team_schema["alternateName"] == "FRC Team 148"
    assert sports_team_schema["foundingDate"] == "1992"
    assert sports_team_schema["location"]["address"]["addressLocality"] == "Greenville"
    assert sports_team_schema["location"]["address"]["addressRegion"] == "Texas"
    assert sports_team_schema["location"]["address"]["addressCountry"] == "USA"
