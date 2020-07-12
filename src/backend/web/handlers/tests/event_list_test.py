import datetime
import re

from bs4 import BeautifulSoup
from google.cloud import ndb
from werkzeug.test import Client

from backend.web.handlers.tests import helpers


def test_bad_year(web_client: Client) -> None:
    resp = web_client.get("/events/9999")
    assert resp.status_code == 404


def test_valid_years_dropdown(web_client: Client) -> None:
    resp = web_client.get("/events")
    assert resp.status_code == 200

    year_dropdown = BeautifulSoup(resp.data, "html.parser").find(id="valid-years")
    assert year_dropdown is not None

    expected_years = list(range(1992, datetime.datetime.now().year + 1))
    assert [
        int(y.string) for y in year_dropdown.contents if y != "\n"
    ] == expected_years


def test_render_event(ndb_client: ndb.Client, web_client: Client) -> None:
    helpers.preseed_event(ndb_client, "2020nyny")

    resp = web_client.get("/events/2020")
    assert resp.status_code == 200

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

    # Event Webcast (none set)
    assert "".join(event_row.find_all("td")[1].stripped_strings) == ""

    # Event Dates
    assert "".join(event_row.find_all("td")[2].strings) == "Mar 1st to Mar 5th, 2020"


def test_render_years_events(web_client: Client, setup_full_year_events) -> None:
    resp = web_client.get("/events/2019")
    assert resp.status_code == 200

    event_types = BeautifulSoup(resp.data, "html.parser").find_all(
        id=re.compile(r"event_label_container_.*")
    )
    assert len(event_types) == 11
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
