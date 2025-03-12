from bs4 import BeautifulSoup
from freezegun import freeze_time
from werkzeug.test import Client

from backend.web.handlers.tests import helpers


def test_get_bad_event_key(web_client: Client) -> None:
    resp = web_client.get("/event/2020nyny")
    assert resp.status_code == 404


def test_render_event(ndb_stub, web_client: Client) -> None:
    helpers.preseed_event("2020nyny")

    resp = web_client.get("/event/2020nyny")
    assert resp.status_code == 200
    assert "max-age=86400" in resp.headers["Cache-Control"]

    soup = BeautifulSoup(resp.data, "html.parser")
    assert soup.find(id="event-name").string == "Test Event 2020"
    assert soup.find(itemprop="startDate").string == "March 1"
    assert soup.find(itemprop="endDate").string == "March 5, 2020"


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


def test_render_full_regional_round_robin(web_client: Client, setup_full_event) -> None:
    setup_full_event("2019cmptx")

    resp = web_client.get("/event/2019cmptx")
    assert resp.status_code == 200

    soup = BeautifulSoup(resp.data, "html.parser")
    assert soup.find(id="event-name").string == "Einstein Field (Houston) 2019"
    assert soup.find(itemprop="startDate").string == "April 20, 2019"
    assert soup.find(itemprop="endDate") is None

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
    assert soup.find(itemprop="startDate").string == "February 26"
    assert soup.find(itemprop="endDate").string == "March 1, 2025"

    district_point_tab = soup.find("a", {"href": "#district_points"})
    assert district_point_tab is None

    regional_point_tab = soup.find("a", {"href": "#cmp-points"})
    assert regional_point_tab is not None
