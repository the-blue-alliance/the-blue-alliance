import bs4
from freezegun import freeze_time
from google.appengine.ext import ndb
from werkzeug.test import Client

from backend.common.models.district import District
from backend.common.models.district_team import DistrictTeam
from backend.web.handlers.tests import helpers


@freeze_time("2021-04-01")
def test_district_list_current_year(web_client: Client, login_gae_admin) -> None:
    resp = web_client.get("/admin/districts")
    assert resp.status_code == 200

    soup = bs4.BeautifulSoup(resp.data, "html.parser")
    assert soup.find("title").contents == ["District List (2021) - TBA Admin"]


def test_district_list(web_client: Client, login_gae_admin) -> None:
    helpers.preseed_district("2020ne")
    resp = web_client.get("/admin/districts/2020")
    assert resp.status_code == 200

    soup = bs4.BeautifulSoup(resp.data, "html.parser")
    assert soup.find("title").contents == ["District List (2020) - TBA Admin"]


def test_district_list_none_for_year(web_client: Client, login_gae_admin) -> None:
    helpers.preseed_district("2020ne")
    resp = web_client.get("/admin/districts/2021")
    assert resp.status_code == 200


def test_district_edit_bad_event(web_client: Client, login_gae_admin) -> None:
    resp = web_client.get("/admin/district/edit/2021asdf")
    assert resp.status_code == 404


def test_district_edit(web_client: Client, login_gae_admin) -> None:
    helpers.preseed_district("2020ne")
    resp = web_client.get("/admin/district/edit/2020ne")
    assert resp.status_code == 200


def test_edit_district(
    web_client: Client, login_gae_admin, ndb_stub, taskqueue_stub
) -> None:
    helpers.preseed_district("2020ne")
    resp = web_client.post(
        "/admin/district/edit/2020ne",
        data={
            "year": "2020",
            "abbreviation": "ne",
            "display_name": "New England",
        },
    )
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/admin/districts/2020"

    district = District.get_by_id("2020ne")
    assert district is not None
    assert district.display_name == "New England"


def test_district_create(web_client: Client, login_gae_admin) -> None:
    resp = web_client.get("/admin/district/create")
    assert resp.status_code == 200


def test_create_district(
    web_client: Client, login_gae_admin, ndb_stub, taskqueue_stub
) -> None:
    resp = web_client.post(
        "/admin/district/edit",
        data={
            "year": "2021",
            "abbreviation": "ne",
            "display_name": "New England",
        },
    )
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/admin/districts/2021"

    district = District.get_by_id("2021ne")
    assert district is not None
    assert district.display_name == "New England"


def test_create_district_invalid_key(
    web_client: Client, login_gae_admin, ndb_stub, taskqueue_stub
) -> None:
    resp = web_client.post(
        "/admin/district/edit",
        data={
            "year": "2020",
            "abbreviation": "ne_",
            "display_name": "New England",
        },
    )
    assert resp.status_code == 400

    assert District.query().count() == 0


def test_district_delete(web_client: Client, login_gae_admin) -> None:
    helpers.preseed_district("2020ne")
    resp = web_client.get("/admin/district/delete/2020ne")
    assert resp.status_code == 200


def test_district_delete_bad_key(web_client: Client, login_gae_admin) -> None:
    resp = web_client.get("/admin/district/delete/2020asdf")
    assert resp.status_code == 404


def test_delete_district(
    web_client: Client, login_gae_admin, ndb_stub, taskqueue_stub
) -> None:
    helpers.preseed_district("2020ne")
    resp = web_client.post("/admin/district/delete/2020ne")
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/admin/districts/2020"

    district = District.get_by_id("2020ne")
    assert district is None

    district_teams = DistrictTeam.query(
        DistrictTeam.district_key == ndb.Key(District, "2020ne")
    ).fetch()
    assert district_teams == []


def test_delete_district_bad_key(
    web_client: Client, login_gae_admin, ndb_stub, taskqueue_stub
) -> None:
    resp = web_client.post("/admin/district/delete/2020ne")
    assert resp.status_code == 404
