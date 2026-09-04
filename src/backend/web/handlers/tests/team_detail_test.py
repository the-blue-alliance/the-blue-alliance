import json
from typing import Generator

from bs4 import BeautifulSoup
from freezegun import freeze_time
from google.appengine.ext import ndb
from werkzeug.test import Client

from backend.common.consts.media_type import MediaType
from backend.common.consts.webcast_status import WebcastStatus
from backend.common.consts.webcast_type import WebcastType
from backend.common.memcache_models.webcast_online_status_memcache import (
    WebcastOnlineStatusMemcache,
)
from backend.common.models.media import Media
from backend.common.models.team import Team
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


@ndb.synctasklet
def preseed_smugmug_photo(team_number: int, year: int) -> Generator:
    yield Media(
        id="smugmug-photo_xxrbgK6",
        media_type_enum=MediaType.SMUGMUG_PHOTO,
        foreign_key="xxrbgK6",
        year=year,
        details_json=json.dumps(
            {
                "title": "Robot on the field",
                "caption": "",
                "web_uri": "https://nefirst.smugmug.com/2026-FIRST-AGE/2026-CMP-BAE/i-xxrbgK6",
                "image_url": "https://photos.smugmug.com/L/x-L.jpg",
                "image_url_med": "https://photos.smugmug.com/M/x-M.jpg",
                "image_url_sm": "https://photos.smugmug.com/S/x-S.jpg",
            }
        ),
        references=[ndb.Key(Team, f"frc{team_number}")],
    ).put_async()


def test_smugmug_photo_in_gallery(web_client: Client, ndb_stub) -> None:
    helpers.preseed_team(254)
    helpers.preseed_event_for_team(254, "2020test")
    preseed_smugmug_photo(254, 2020)

    resp = web_client.get("/team/254/2020")
    assert resp.status_code == 200
    soup = BeautifulSoup(resp.data, "html.parser")

    thumbnail = soup.find(
        "a", class_="gallery", href="https://photos.smugmug.com/L/x-L.jpg"
    )
    assert thumbnail is not None
    assert "https://photos.smugmug.com/M/x-M.jpg" in thumbnail.find("span")["style"]

    caption = soup.find(
        "a",
        href="https://nefirst.smugmug.com/2026-FIRST-AGE/2026-CMP-BAE/i-xxrbgK6",
    )
    assert caption is not None
    assert caption.text == "Robot on the field"


@ndb.synctasklet
def preseed_smugmug_album(team_number: int, year: int) -> Generator:
    yield Media(
        id="smugmug-album_4RWMLM",
        media_type_enum=MediaType.SMUGMUG_ALBUM,
        foreign_key="4RWMLM",
        year=year,
        details_json=json.dumps(
            {
                "title": "2026 FIRST Championship - BAE Systems",
                "web_uri": "https://nefirst.smugmug.com/2026-FIRST-AGE/2026-CMP-BAE",
                "image_count": 81,
                "cover_url": "https://photos.smugmug.com/L/cover-L.png",
                "cover_url_med": "https://photos.smugmug.com/M/cover-M.png",
                "cover_url_sm": "https://photos.smugmug.com/S/cover-S.png",
            }
        ),
        references=[ndb.Key(Team, f"frc{team_number}")],
    ).put_async()


def test_smugmug_album_in_photo_galleries(web_client: Client, ndb_stub) -> None:
    helpers.preseed_team(254)
    helpers.preseed_event_for_team(254, "2020test")
    preseed_smugmug_album(254, 2020)

    resp = web_client.get("/team/254/2020")
    assert resp.status_code == 200
    soup = BeautifulSoup(resp.data, "html.parser")

    assert soup.find(id="photo-galleries") is not None

    links = soup.find_all(
        "a", href="https://nefirst.smugmug.com/2026-FIRST-AGE/2026-CMP-BAE"
    )
    assert len(links) == 2

    cover, caption = links
    assert "https://photos.smugmug.com/M/cover-M.png" in cover.find("span")["style"]
    assert caption.text == "2026 FIRST Championship - BAE Systems"
    assert "81 photos" in caption.parent.text

    # An album alone must not fall through to the empty-media message
    assert "No photos or videos for team" not in resp.get_data(as_text=True)


def test_no_smugmug_album(web_client: Client, ndb_stub) -> None:
    helpers.preseed_team(254)
    helpers.preseed_event_for_team(254, "2020test")

    resp = web_client.get("/team/254/2020")
    assert resp.status_code == 200
    soup = BeautifulSoup(resp.data, "html.parser")
    assert soup.find(id="photo-galleries") is None
