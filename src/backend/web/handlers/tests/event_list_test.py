import datetime
import re

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


def test_bad_year(web_client: Client) -> None:
    resp = web_client.get("/events/9999")
    assert resp.status_code == 404


def test_valid_years_dropdown(ndb_stub, web_client: Client) -> None:
    resp = web_client.get("/events")
    assert resp.status_code == 200

    year_dropdown = BeautifulSoup(resp.data, "html.parser").find(id="valid-years")
    assert year_dropdown is not None

    expected_years = list(reversed(range(1992, datetime.datetime.now().year + 1)))
    assert [
        int(y.string) for y in year_dropdown.contents if y != "\n"
    ] == expected_years


@freeze_time("2020-04-02")
def test_render_event_short_cache(ndb_stub, web_client: Client) -> None:
    helpers.preseed_event("2020nyny")

    resp = web_client.get("/events/2020")
    assert resp.status_code == 200
    assert "max-age=300" in resp.headers["Cache-Control"]


def test_render_event(ndb_stub, web_client: Client) -> None:
    helpers.preseed_event("2020nyny")

    resp = web_client.get("/events/2020")
    assert resp.status_code == 200
    assert "max-age=86400" in resp.headers["Cache-Control"]

    event_types = BeautifulSoup(resp.data, "html.parser").find_all(
        id=re.compile(r"event_label_container_.*")
    )
    assert len(event_types) == 1
    container = event_types[0]
    assert container["id"] == "event_label_container_offseason"

    title = container.find("h2")
    assert title["id"] == "offseason"
    assert "".join(title.strings) == "Offseason 1 Events"

    table = container.find("table")
    rows = table.find("tbody").find_all("tr")
    assert len(rows) == 1
    event_row = rows[0]

    # Event Name
    assert "".join(event_row.find_all("td")[0].stripped_strings) == "Test Event"

    # Event Webcast
    assert "".join(event_row.find_all("td")[1].stripped_strings) == "Offline"

    # Event Dates
    assert "".join(event_row.find_all("td")[2].strings) == "Mar 1st to Mar 5th, 2020"


@freeze_time("2020-03-02")
def test_render_event_offline_webcast_has_scheduled_start_tooltip(
    ndb_stub, web_client: Client
) -> None:
    helpers.preseed_event("2020nyny")

    webcast_status = Webcast(
        type=WebcastType.TWITCH,
        channel="firstinspires",
        status=WebcastStatus.OFFLINE,
        stream_title="Upcoming Stream",
        viewer_count=None,
        scheduled_start_time_utc="2020-03-02T18:00:00Z",
    )
    WebcastOnlineStatusMemcache(webcast_status).put(webcast_status)

    resp = web_client.get("/events/2020")
    assert resp.status_code == 200

    event_types = BeautifulSoup(resp.data, "html.parser").find_all(
        id=re.compile(r"event_label_container_.*")
    )
    assert len(event_types) == 1

    row = event_types[0].find("table").find("tbody").find("tr")
    webcast_link = row.find_all("td")[1].find("a", class_="tba-webcast-offline-tooltip")
    assert webcast_link is not None
    assert webcast_link.get("data-scheduled-start-utc") == "2020-03-02T18:00:00Z"
    assert webcast_link.get("title") == "scheduled to start at"
    assert "tooltip" in webcast_link.get("rel", [])


def test_render_years_events(
    ndb_stub, web_client: Client, setup_full_year_events
) -> None:
    resp = web_client.get("/events/2019")
    assert resp.status_code == 200

    event_types = BeautifulSoup(resp.data, "html.parser").find_all(
        id=re.compile(r"event_label_container_.*")
    )
    event_type_names = ["".join(t.find("h2").strings) for t in event_types]
    assert event_type_names == [
        "Week 1 17 Events",
        "Week 2 33 Events",
        "Week 3 33 Events",
        "Week 4 32 Events",
        "Week 5 31 Events",
        "Week 6 22 Events",
        "Week 7 11 Events",
        "FIRST Championship - Houston 7 Events",
        "FIRST Championship - Detroit 7 Events",
        "Preseason 10 Events",
        "Offseason 100 Events",
    ]
