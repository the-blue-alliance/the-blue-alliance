import datetime

from bs4 import BeautifulSoup
from werkzeug.test import Client

from backend.web.handlers.tests import helpers


def test_get_bad_year(ndb_stub, web_client: Client) -> None:
    helpers.preseed_regional("2020nyc")
    resp = web_client.get("/events/regional/2022")
    assert resp.status_code == 404


def test_render_regionals(ndb_stub, web_client: Client) -> None:
    helpers.preseed_regional("2020nyc")
    resp = web_client.get("/events/regional/2020")
    assert resp.status_code == 200
    assert "max-age=86400" in resp.headers["Cache-Control"]

    soup = BeautifulSoup(resp.data, "html.parser")

    regional_header = soup.find(id="regional-header")
    assert "".join(regional_header.strings) == "2020 Regional Events 5 Events"


def test_valid_years_dropdown(ndb_stub, web_client: Client) -> None:
    helpers.preseed_regional("2020nyc")

    resp = web_client.get("/events/regional/2020")
    assert resp.status_code == 200

    year_dropdown = BeautifulSoup(resp.data, "html.parser").find(id="valid-years")
    assert year_dropdown is not None

    expected_years = list(reversed(range(1992, datetime.datetime.now().year + 1)))
    assert [
        int(y.string) for y in year_dropdown.contents if y != "\n"
    ] == expected_years


def test_valid_districts_dropdown(ndb_stub, web_client: Client) -> None:
    helpers.preseed_regional("2020nyc")
    [helpers.preseed_district(f"2020{district}") for district in ["ne", "fim", "mar"]]

    resp = web_client.get("/events/regional/2020")
    assert resp.status_code == 200

    district_dropdown = BeautifulSoup(resp.data, "html.parser").find(
        id="valid-districts"
    )
    assert district_dropdown is not None

    expected_districts = ["All Events", "FIM", "MAR", "NE"]
    assert [
        y.string for y in district_dropdown.contents if y != "\n"
    ] == expected_districts
