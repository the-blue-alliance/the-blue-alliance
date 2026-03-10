import bs4
from freezegun import freeze_time
from werkzeug.test import Client

from backend.common.models.event import Event
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


def test_invalid_event_delete(
    web_client: Client, login_gae_admin, taskqueue_stub
) -> None:
    helpers.preseed_event("2025tempclone-356125237")
    resp = web_client.post("/admin/event/2025tempclone-356125237/delete")
    assert resp.status_code == 302


def test_add_webcast_via_url_youtube(
    web_client: Client, login_gae_admin, taskqueue_stub
) -> None:
    helpers.preseed_event("2020nyny")
    resp = web_client.post(
        "/admin/event/add_webcast/2020nyny",
        data={
            "webcast_url": "https://www.youtube.com/watch?v=abc123defgh",
            "webcast_date": "",
            "csrf_token": "test",
        },
    )
    assert resp.status_code == 302
    event = Event.get_by_id("2020nyny")
    assert event is not None
    webcasts = event.webcast
    youtube_webcasts = [w for w in webcasts if w["type"] == "youtube"]
    assert len(youtube_webcasts) == 1
    assert youtube_webcasts[0]["channel"] == "abc123defgh"


def test_add_webcast_via_url_twitch(
    web_client: Client, login_gae_admin, taskqueue_stub
) -> None:
    helpers.preseed_event("2020nyny")
    resp = web_client.post(
        "/admin/event/add_webcast/2020nyny",
        data={
            "webcast_url": "https://www.twitch.tv/firstinspires2",
            "webcast_date": "",
            "csrf_token": "test",
        },
    )
    assert resp.status_code == 302
    event = Event.get_by_id("2020nyny")
    assert event is not None
    webcasts = event.webcast
    twitch_webcasts = [w for w in webcasts if w["type"] == "twitch"]
    assert any(w["channel"] == "firstinspires2" for w in twitch_webcasts)


def test_add_webcast_via_url_invalid(web_client: Client, login_gae_admin) -> None:
    helpers.preseed_event("2020nyny")
    resp = web_client.post(
        "/admin/event/add_webcast/2020nyny",
        data={
            "webcast_url": "https://example.com/not-a-known-stream",
            "webcast_date": "",
            "csrf_token": "test",
        },
    )
    # Should redirect back with an error parameter
    assert resp.status_code == 302
    assert (
        b"webcast_url_error=1" in resp.data
        or "webcast_url_error=1" in resp.headers.get("Location", "")
    )


def test_add_webcast_via_manual_fields(
    web_client: Client, login_gae_admin, taskqueue_stub
) -> None:
    helpers.preseed_event("2020nyny")
    resp = web_client.post(
        "/admin/event/add_webcast/2020nyny",
        data={
            "webcast_url": "",
            "webcast_type": "twitch",
            "webcast_channel": "manualtwitchchannel",
            "webcast_file": "",
            "webcast_date": "",
            "csrf_token": "test",
        },
    )
    assert resp.status_code == 302
    event = Event.get_by_id("2020nyny")
    assert event is not None
    webcasts = event.webcast
    assert any(
        w["type"] == "twitch" and w["channel"] == "manualtwitchchannel"
        for w in webcasts
    )


def test_webcast_form_has_url_field(
    web_client: Client, login_gae_admin, setup_full_event
) -> None:
    setup_full_event("2019nyny")
    resp = web_client.get("/admin/event/2019nyny")
    assert resp.status_code == 200
    soup = bs4.BeautifulSoup(resp.data, "html.parser")
    url_input = soup.find("input", {"name": "webcast_url"})
    assert url_input is not None


def test_webcast_form_dropdown_order(
    web_client: Client, login_gae_admin, setup_full_event
) -> None:
    setup_full_event("2019nyny")
    resp = web_client.get("/admin/event/2019nyny")
    assert resp.status_code == 200
    soup = bs4.BeautifulSoup(resp.data, "html.parser")
    select = soup.find("select", {"name": "webcast_type"})
    assert select is not None
    options = [opt["value"] for opt in select.find_all("option")]
    assert options[0] == "youtube"
    assert options[1] == "twitch"
