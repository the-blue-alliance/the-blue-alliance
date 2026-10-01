import datetime

from bs4 import BeautifulSoup
from freezegun import freeze_time
from werkzeug.test import Client

from backend.common.models.regional_champs_pool import RegionalChampsPool
from backend.common.models.regional_pool_advancement import (
    ChampionshipStatus,
    TeamRegionalPoolAdvancement,
)
from backend.common.models.regional_pool_ranking import RegionalPoolRanking
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


def test_invalid_year(ndb_stub, web_client: Client) -> None:
    resp = web_client.get("/events/regional/1800")
    assert resp.status_code == 404


@freeze_time("2025-03-05")
def test_render_regionals_current_season_with_pool(
    ndb_stub, web_client: Client
) -> None:
    helpers.preseed_regional("2025nyc")
    RegionalChampsPool(
        id=RegionalChampsPool.render_key_name(2025),
        year=2025,
        rankings=[
            RegionalPoolRanking(
                rank=1,
                team_key="frc1",
                point_total=50,
                rookie_bonus=0,
                single_event_bonus=0,
                adjustments=5,
                event_points=[],
            )
        ],
        advancement={
            "frc1": TeamRegionalPoolAdvancement(
                cmp=True, cmp_status=ChampionshipStatus.POOL_QUALIFIED
            )
        },
    ).put()

    resp = web_client.get("/events/regional")
    assert resp.status_code == 200
    assert "max-age=900" in resp.headers["Cache-Control"]
    soup = BeautifulSoup(resp.data, "html.parser")
    assert soup.find(id="rankings") is not None
