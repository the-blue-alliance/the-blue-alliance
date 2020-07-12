from bs4 import BeautifulSoup
from google.cloud import ndb
from werkzeug.test import Client

from backend.web.handlers.tests import helpers


def test_get_bad_event_key(web_client: Client) -> None:
    resp = web_client.get("/event/2020nyny")
    assert resp.status_code == 404


def test_render_event(ndb_client: ndb.Client, web_client: Client) -> None:
    helpers.preseed_event(ndb_client, "2020nyny")

    resp = web_client.get("/event/2020nyny")
    assert resp.status_code == 200

    soup = BeautifulSoup(resp.data, "html.parser")
    assert soup.find(id="event-name").string == "Test Event 2020"
    assert soup.find(itemprop="startDate").string == "March 1"
    assert soup.find(itemprop="endDate").string == "March 5, 2020"


def test_render_full_regional(web_client: Client, setup_full_event) -> None:
    setup_full_event("2019nyny")

    resp = web_client.get("/event/2019nyny")
    assert resp.status_code == 200

    soup = BeautifulSoup(resp.data, "html.parser")
    assert soup.find(id="event-name").string == "New York City Regional 2019"
    assert soup.find(itemprop="startDate").string == "April 4"
    assert soup.find(itemprop="endDate").string == "April 7, 2019"

    qual_match_table = soup.find(id="qual-match-table")
    qual_matches = qual_match_table.find("tbody").find_all("tr")
    assert len(qual_matches) > 1

    elim_match_table = soup.find(id="elim-match-table")
    elim_matches = elim_match_table.find("tbody").find_all("tr")
    assert len(elim_matches) > 1

    alliances_table = soup.find(id="event-alliances")
    assert len(alliances_table.find_all("tr")) > 1
