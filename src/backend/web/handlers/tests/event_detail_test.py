import json

from bs4 import BeautifulSoup
from freezegun import freeze_time
from google.appengine.ext import ndb
from werkzeug.test import Client

from backend.common.consts.alliance_color import AllianceColor
from backend.common.consts.comp_level import CompLevel
from backend.common.consts.webcast_status import WebcastStatus
from backend.common.consts.webcast_type import WebcastType
from backend.common.memcache_models.webcast_online_status_memcache import (
    WebcastOnlineStatusMemcache,
)
from backend.common.models.alliance import MatchAlliance
from backend.common.models.event import Event
from backend.common.models.event_details import EventDetails
from backend.common.models.match import Match
from backend.common.models.webcast import Webcast
from backend.web.handlers.tests import helpers


def test_get_bad_event_key(web_client: Client) -> None:
    resp = web_client.get("/event/2020nyny")
    assert resp.status_code == 404


def test_render_event(ndb_stub, web_client: Client) -> None:
    helpers.preseed_event("2020nyny")

    resp = web_client.get("/event/2020nyny")
    assert resp.status_code == 200
    assert "max-age=21600" in resp.headers["Cache-Control"]

    soup = BeautifulSoup(resp.data, "html.parser")
    assert soup.find(id="event-name").string == "Test Event 2020"


def test_render_2026_event_with_legacy_insight_data(
    ndb_stub, web_client: Client
) -> None:
    helpers.preseed_event("2026test")

    legacy_2026_insights = {"backfill_pending": True}

    EventDetails(
        id="2026test",
        insights={"qual": legacy_2026_insights, "playoff": {}},
    ).put()

    resp = web_client.get("/event/2026test")
    assert resp.status_code == 200

    body = resp.get_data(as_text=True)
    assert "Auto Win Conversion" in body
    assert "Fuel Statistics" in body
    assert "Tower Statistics" in body


@freeze_time("2020-03-02")
def test_render_short_cache(ndb_stub, web_client: Client) -> None:
    helpers.preseed_event("2020nyny")

    resp = web_client.get("/event/2020nyny")
    assert resp.status_code == 200
    assert "max-age=61" in resp.headers["Cache-Control"]


def test_render_full_regional(web_client: Client, setup_full_event) -> None:
    setup_full_event("2019nyny")

    resp = web_client.get("/event/2019nyny")
    assert resp.status_code == 200

    soup = BeautifulSoup(resp.data, "html.parser")
    assert soup.find(id="event-name").string == "New York City Regional 2019"

    qual_match_table = soup.find(id="qual-match-table")
    qual_matches = qual_match_table.find("tbody").find_all("tr")
    assert len(qual_matches) > 1

    elim_match_table = soup.find(id="elim-match-table")
    elim_matches = elim_match_table.find("tbody").find_all("tr")
    assert len(elim_matches) > 1

    alliances_table = soup.find(id="event-alliances")
    assert len(alliances_table.find_all("tr")) > 1


@freeze_time("2020-03-02")
def test_render_event_offline_webcast_has_scheduled_start_tooltip(
    ndb_stub, web_client: Client
) -> None:
    helpers.preseed_event("2020nyny")

    Match(
        id="2020nyny_qm1",
        year=2020,
        comp_level=CompLevel.QM,
        set_number=1,
        match_number=1,
        event=ndb.Key(Event, "2020nyny"),
        alliances_json=json.dumps(
            {
                AllianceColor.RED: MatchAlliance(
                    teams=["frc1", "frc2", "frc3"], score=-1
                ),
                AllianceColor.BLUE: MatchAlliance(
                    teams=["frc4", "frc5", "frc6"], score=-1
                ),
            }
        ),
    ).put()

    webcast_status = Webcast(
        type=WebcastType.TWITCH,
        channel="firstinspires",
        status=WebcastStatus.OFFLINE,
        stream_title="Upcoming Stream",
        viewer_count=None,
        scheduled_start_time_utc="2020-03-02T18:00:00Z",
    )
    WebcastOnlineStatusMemcache(webcast_status).put(webcast_status)

    resp = web_client.get("/event/2020nyny")
    assert resp.status_code == 200

    soup = BeautifulSoup(resp.data, "html.parser")
    offline_button = soup.select_one(".panel-heading a.tba-webcast-offline-tooltip")
    assert offline_button is not None
    assert offline_button.get("data-scheduled-start-utc") == "2020-03-02T18:00:00Z"
    assert offline_button.get("title") == "scheduled to start at"
    assert "tooltip" in offline_button.get("rel", [])


def test_render_full_regional_round_robin(web_client: Client, setup_full_event) -> None:
    setup_full_event("2019cmptx")

    resp = web_client.get("/event/2019cmptx")
    assert resp.status_code == 200

    soup = BeautifulSoup(resp.data, "html.parser")
    assert soup.find(id="event-name").string == "Einstein Field (Houston) 2019"

    qual_match_table = soup.find(id="qual-match-table")
    assert qual_match_table is None

    elim_match_table = soup.find(id="elim-match-table")
    elim_matches = elim_match_table.find("tbody").find_all("tr")
    assert len(elim_matches) > 1

    alliances_table = soup.find(id="event-alliances")
    assert len(alliances_table.find_all("tr")) > 1


def test_render_legacy_double_elim(web_client: Client, test_data_importer) -> None:
    test_data_importer.import_event(__file__, "data/2017wiwi.json")
    test_data_importer.import_match_list(__file__, "data/2017wiwi_matches.json")

    resp = web_client.get("/event/2017wiwi")
    assert resp.status_code == 200

    soup = BeautifulSoup(resp.data, "html.parser")

    qual_match_table = soup.find(id="qual-match-table")
    qual_matches = qual_match_table.find("tbody").find_all("tr")
    assert len(qual_matches) > 1

    elim_match_table = soup.find(id="elim-match-table")
    elim_matches = elim_match_table.find("tbody").find_all("tr")
    assert len(elim_matches) > 1


def test_render_double_elim(web_client: Client, test_data_importer) -> None:
    test_data_importer.import_event(__file__, "data/2022cctest.json")
    test_data_importer.import_match_list(__file__, "data/2022cctest_matches.json")
    test_data_importer.import_event_playoff_advancement(
        __file__, "data/2022cctest_advancement.json", "2022cctest"
    )

    resp = web_client.get("/event/2022cctest")
    assert resp.status_code == 200

    soup = BeautifulSoup(resp.data, "html.parser")

    qual_match_table = soup.find(id="qual-match-table")
    assert qual_match_table is None

    elim_match_table = soup.find(id="elim-match-table")
    elim_matches = elim_match_table.find("tbody").find_all("tr")
    assert len(elim_matches) > 1

    double_elim_bracket = soup.find(id="double-elim-bracket-table")
    assert double_elim_bracket is not None


def test_render_regional_cmp_points(web_client: Client, test_data_importer) -> None:
    test_data_importer.import_full_event(__file__, "2025mndu")

    resp = web_client.get("/event/2025mndu")
    assert resp.status_code == 200

    soup = BeautifulSoup(resp.data, "html.parser")
    assert soup.find(id="event-name").string == "Lake Superior Regional 2025"

    district_point_tab = soup.find("a", {"href": "#district_points"})
    assert district_point_tab is None

    regional_point_tab = soup.find("a", {"href": "#cmp-points"})
    assert regional_point_tab is not None


def test_schema_org_sports_event(ndb_stub, web_client: Client) -> None:
    """Test that event pages include schema.org SportsEvent JSON-LD markup."""
    helpers.preseed_event("2020nyny")

    resp = web_client.get("/event/2020nyny")
    assert resp.status_code == 200

    soup = BeautifulSoup(resp.data, "html.parser")

    # Find the JSON-LD script tag
    schema_scripts = soup.find_all("script", {"type": "application/ld+json"})
    assert len(schema_scripts) >= 1

    # Find the SportsEvent schema
    sports_event_schema = None
    for script in schema_scripts:
        data = json.loads(script.string)
        if data.get("@type") == "SportsEvent":
            sports_event_schema = data
            break

    assert sports_event_schema is not None
    assert sports_event_schema["@context"] == "https://schema.org"
    assert sports_event_schema["@type"] == "SportsEvent"
    assert sports_event_schema["name"] == "Test Event 2020"
    assert sports_event_schema["sport"] == "Robotics"
    assert sports_event_schema["startDate"] == "2020-03-01"
    assert sports_event_schema["endDate"] == "2020-03-05"
    assert sports_event_schema["eventStatus"] == "https://schema.org/EventScheduled"
    assert (
        sports_event_schema["eventAttendanceMode"]
        == "https://schema.org/OfflineEventAttendanceMode"
    )
    assert (
        sports_event_schema["url"] == "https://www.thebluealliance.com/event/2020nyny"
    )

    # Check organizer
    assert sports_event_schema["organizer"]["@type"] == "SportsOrganization"
    assert sports_event_schema["organizer"]["name"] == "FIRST"
    assert sports_event_schema["organizer"]["url"] == "https://www.firstinspires.org"


def test_schema_org_sports_event_with_location(
    ndb_stub, web_client: Client, test_data_importer
) -> None:
    """Test that event pages include location in schema.org markup when available."""
    test_data_importer.import_full_event(__file__, "2025mndu")

    resp = web_client.get("/event/2025mndu")
    assert resp.status_code == 200

    soup = BeautifulSoup(resp.data, "html.parser")

    # Find the SportsEvent schema
    schema_scripts = soup.find_all("script", {"type": "application/ld+json"})
    sports_event_schema = None
    for script in schema_scripts:
        data = json.loads(script.string)
        if data.get("@type") == "SportsEvent":
            sports_event_schema = data
            break

    assert sports_event_schema is not None
    assert "location" in sports_event_schema
    assert sports_event_schema["location"]["@type"] == "Place"
    assert "address" in sports_event_schema["location"]
    assert sports_event_schema["location"]["address"]["@type"] == "PostalAddress"


def test_render_event_with_b_team_coprs(ndb_stub, web_client: Client) -> None:
    """Test that event detail page handles B teams in COPR data without crashing."""
    helpers.preseed_event("2020nyny")
    EventDetails(
        id="2020nyny",
        coprs={"Cargo": {"frc6884B": 10.5, "frc254": 20.0}},
    ).put()

    resp = web_client.get("/event/2020nyny")
    assert resp.status_code == 200
