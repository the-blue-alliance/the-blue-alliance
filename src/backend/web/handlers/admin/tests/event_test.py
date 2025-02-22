import bs4
from freezegun import freeze_time
from werkzeug.test import Client

from backend.web.handlers.tests import helpers


def test_event_list_not_logged_in(web_client: Client) -> None:
    resp = web_client.get("/admin/events")
    assert resp.status_code == 401


def test_event_list_not_admin(web_client: Client, login_gae_user) -> None:
    resp = web_client.get("/admin/events")
    assert resp.status_code == 401


@freeze_time("2021-04-01")
def test_event_list_current_year(web_client: Client, login_gae_admin) -> None:
    resp = web_client.get("/admin/events")
    assert resp.status_code == 200

    soup = bs4.BeautifulSoup(resp.data, "html.parser")
    assert soup.find("title").contents == ["Event List (2021) - TBA Admin"]


def test_event_list(web_client: Client, login_gae_admin) -> None:
    helpers.preseed_event("2020nyny")
    resp = web_client.get("/admin/events/2020")
    assert resp.status_code == 200

    soup = bs4.BeautifulSoup(resp.data, "html.parser")
    assert soup.find("title").contents == ["Event List (2020) - TBA Admin"]


def test_event_list_none_for_year(web_client: Client, login_gae_admin) -> None:
    helpers.preseed_event("2020nyny")
    resp = web_client.get("/admin/events/2021")
    assert resp.status_code == 200


def test_event_detail_bad_event(web_client: Client, login_gae_admin) -> None:
    helpers.preseed_event("2020nyny")
    resp = web_client.get("/admin/event/asdf")
    assert resp.status_code == 404


def test_event_detail_not_found(web_client: Client, login_gae_admin) -> None:
    resp = web_client.get("/admin/event/2020nyny")
    assert resp.status_code == 404


def test_event_detail(web_client: Client, login_gae_admin, setup_full_event) -> None:
    setup_full_event("2019nyny")
    resp = web_client.get("/admin/event/2019nyny")
    assert resp.status_code == 200


def test_invalid_event_delete(web_client: Client, login_gae_admin, taskqueue_stub) -> None:
    helpers.preseed_event("2025tempclone-356125237")
    resp = web_client.post("/admin/event/2025tempclone-356125237/delete")
    assert resp.status_code == 302
