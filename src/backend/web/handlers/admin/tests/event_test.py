import json
from datetime import datetime
from unittest.mock import patch

import bs4
from freezegun import freeze_time
from google.appengine.ext import ndb
from werkzeug.test import Client

from backend.common.consts.event_type import EventType
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


def test_update_webcast_date_bad_event(web_client: Client, login_gae_admin) -> None:
    resp = web_client.post(
        "/admin/event/update_webcast_date/2020nyny",
        data={
            "type": "youtube",
            "channel": "abc123",
            "index": "1",
            "csrf_token": "test",
        },
    )
    assert resp.status_code == 404


def test_update_webcast_date_non_youtube(
    web_client: Client, login_gae_admin, taskqueue_stub
) -> None:
    helpers.preseed_event("2020nyny")
    resp = web_client.post(
        "/admin/event/update_webcast_date/2020nyny",
        data={
            "type": "twitch",
            "channel": "robosportsnetwork",
            "index": "1",
            "csrf_token": "test",
        },
    )
    assert resp.status_code == 400


def test_update_webcast_date_success(
    web_client: Client, login_gae_admin, taskqueue_stub
) -> None:
    Event(
        id="2020nyny",
        event_short="nyny",
        year=2020,
        name="Test Event",
        event_type_enum=EventType.OFFSEASON,
        start_date=datetime(2020, 3, 1),
        end_date=datetime(2020, 3, 5),
        webcast_json=json.dumps([{"type": "youtube", "channel": "abc123defgh"}]),
    ).put()

    with patch(
        "backend.web.handlers.admin.event.YouTubeVideoHelper.get_scheduled_start_time"
    ) as mock_get_date:
        mock_future = ndb.Future()
        mock_future.set_result("2020-03-01")
        mock_get_date.return_value = mock_future

        resp = web_client.post(
            "/admin/event/update_webcast_date/2020nyny",
            data={
                "type": "youtube",
                "channel": "abc123defgh",
                "index": "1",
                "csrf_token": "test",
            },
        )

    assert resp.status_code == 302
    event = Event.get_by_id("2020nyny")
    assert event is not None
    webcasts = event.webcast
    youtube_webcasts = [w for w in webcasts if w["type"] == "youtube"]
    assert len(youtube_webcasts) == 1
    assert youtube_webcasts[0]["date"] == "2020-03-01"


def test_update_webcast_date_no_date_returned(
    web_client: Client, login_gae_admin, taskqueue_stub
) -> None:
    Event(
        id="2020nyny",
        event_short="nyny",
        year=2020,
        name="Test Event",
        event_type_enum=EventType.OFFSEASON,
        start_date=datetime(2020, 3, 1),
        end_date=datetime(2020, 3, 5),
        webcast_json=json.dumps([{"type": "youtube", "channel": "abc123defgh"}]),
    ).put()

    with patch(
        "backend.web.handlers.admin.event.YouTubeVideoHelper.get_scheduled_start_time"
    ) as mock_get_date:
        mock_future = ndb.Future()
        mock_future.set_result(None)
        mock_get_date.return_value = mock_future

        resp = web_client.post(
            "/admin/event/update_webcast_date/2020nyny",
            data={
                "type": "youtube",
                "channel": "abc123defgh",
                "index": "1",
                "csrf_token": "test",
            },
        )

    assert resp.status_code == 302
    event = Event.get_by_id("2020nyny")
    assert event is not None
    webcasts = event.webcast
    youtube_webcasts = [w for w in webcasts if w["type"] == "youtube"]
    assert len(youtube_webcasts) == 1
    assert "date" not in youtube_webcasts[0]


def test_update_date_button_shown_for_youtube(
    web_client: Client, login_gae_admin, taskqueue_stub
) -> None:
    Event(
        id="2020nyny",
        event_short="nyny",
        year=2020,
        name="Test Event",
        event_type_enum=EventType.OFFSEASON,
        start_date=datetime(2020, 3, 1),
        end_date=datetime(2020, 3, 5),
        webcast_json=json.dumps(
            [
                {"type": "youtube", "channel": "abc123defgh"},
                {"type": "twitch", "channel": "firstinspires"},
            ]
        ),
    ).put()

    resp = web_client.get("/admin/event/2020nyny")
    assert resp.status_code == 200
    soup = bs4.BeautifulSoup(resp.data, "html.parser")
    update_date_buttons = [
        btn for btn in soup.find_all("button") if "Update Date" in btn.get_text()
    ]
    assert len(update_date_buttons) == 1


def test_refresh_online_status_button_uses_force_param(
    web_client: Client, login_gae_admin, setup_full_event
) -> None:
    setup_full_event("2019nyny")

    resp = web_client.get("/admin/event/2019nyny")
    assert resp.status_code == 200

    soup = bs4.BeautifulSoup(resp.data, "html.parser")
    refresh_link = soup.find(
        "a", href="/tasks/do/update_webcast_online_status/2019nyny?force=1"
    )
    assert refresh_link is not None


def test_cleanup_youtube_webcasts_not_found_event(
    web_client: Client, login_gae_admin, taskqueue_stub
) -> None:
    resp = web_client.post(
        "/admin/event/cleanup_youtube_webcasts/2020nyny",
        data={"csrf_token": "test"},
    )
    assert resp.status_code == 404


def test_cleanup_youtube_webcasts_no_youtube_webcasts(
    web_client: Client, login_gae_admin, taskqueue_stub
) -> None:
    Event(
        id="2020nyny",
        event_short="nyny",
        year=2020,
        name="Test Event",
        event_type_enum=EventType.OFFSEASON,
        start_date=datetime(2020, 3, 1),
        end_date=datetime(2020, 3, 5),
        webcast_json=json.dumps([{"type": "twitch", "channel": "firstinspires"}]),
    ).put()

    resp = web_client.post(
        "/admin/event/cleanup_youtube_webcasts/2020nyny",
        data={"csrf_token": "test"},
    )
    assert resp.status_code == 302
    event = Event.get_by_id("2020nyny")
    assert event is not None
    assert len(event.webcast) == 1


def test_cleanup_youtube_webcasts_removes_invalid(
    web_client: Client, login_gae_admin, taskqueue_stub
) -> None:
    Event(
        id="2020nyny",
        event_short="nyny",
        year=2020,
        name="Test Event",
        event_type_enum=EventType.OFFSEASON,
        start_date=datetime(2020, 3, 1),
        end_date=datetime(2020, 3, 5),
        webcast_json=json.dumps(
            [
                {"type": "youtube", "channel": "invalid_id"},
                {"type": "twitch", "channel": "firstinspires"},
            ]
        ),
    ).put()

    with patch(
        "backend.web.handlers.admin.event.YouTubeVideoHelper.get_video_details_batch"
    ) as mock_batch:
        mock_future = ndb.Future()
        mock_future.set_result({})
        mock_batch.return_value = mock_future

        resp = web_client.post(
            "/admin/event/cleanup_youtube_webcasts/2020nyny",
            data={"csrf_token": "test"},
        )

    assert resp.status_code == 302
    event = Event.get_by_id("2020nyny")
    assert event is not None
    webcasts = event.webcast
    youtube_webcasts = [w for w in webcasts if w["type"] == "youtube"]
    assert len(youtube_webcasts) == 0
    twitch_webcasts = [w for w in webcasts if w["type"] == "twitch"]
    assert len(twitch_webcasts) == 1


def test_cleanup_youtube_webcasts_updates_date(
    web_client: Client, login_gae_admin, taskqueue_stub
) -> None:
    Event(
        id="2020nyny",
        event_short="nyny",
        year=2020,
        name="Test Event",
        event_type_enum=EventType.OFFSEASON,
        start_date=datetime(2020, 3, 1),
        end_date=datetime(2020, 3, 5),
        webcast_json=json.dumps([{"type": "youtube", "channel": "abc123defgh"}]),
    ).put()

    with patch(
        "backend.web.handlers.admin.event.YouTubeVideoHelper.get_video_details_batch"
    ) as mock_batch:
        mock_future = ndb.Future()
        mock_future.set_result(
            {
                "abc123defgh": {
                    "video_id": "abc123defgh",
                    "title": "",
                    "scheduled_start_time": "2020-03-01",
                }
            }
        )
        mock_batch.return_value = mock_future

        resp = web_client.post(
            "/admin/event/cleanup_youtube_webcasts/2020nyny",
            data={"csrf_token": "test"},
        )

    assert resp.status_code == 302
    event = Event.get_by_id("2020nyny")
    assert event is not None
    webcasts = event.webcast
    youtube_webcasts = [w for w in webcasts if w["type"] == "youtube"]
    assert len(youtube_webcasts) == 1
    assert youtube_webcasts[0]["date"] == "2020-03-01"


def test_cleanup_youtube_webcasts_no_date_unchanged(
    web_client: Client, login_gae_admin, taskqueue_stub
) -> None:
    Event(
        id="2020nyny",
        event_short="nyny",
        year=2020,
        name="Test Event",
        event_type_enum=EventType.OFFSEASON,
        start_date=datetime(2020, 3, 1),
        end_date=datetime(2020, 3, 5),
        webcast_json=json.dumps([{"type": "youtube", "channel": "abc123defgh"}]),
    ).put()

    with patch(
        "backend.web.handlers.admin.event.YouTubeVideoHelper.get_video_details_batch"
    ) as mock_batch:
        mock_future = ndb.Future()
        mock_future.set_result(
            {"abc123defgh": {"video_id": "abc123defgh", "title": ""}}
        )
        mock_batch.return_value = mock_future

        resp = web_client.post(
            "/admin/event/cleanup_youtube_webcasts/2020nyny",
            data={"csrf_token": "test"},
        )

    assert resp.status_code == 302
    event = Event.get_by_id("2020nyny")
    assert event is not None
    webcasts = event.webcast
    youtube_webcasts = [w for w in webcasts if w["type"] == "youtube"]
    assert len(youtube_webcasts) == 1
    assert "date" not in youtube_webcasts[0]


def test_cleanup_youtube_webcasts_button_shown(
    web_client: Client, login_gae_admin, taskqueue_stub
) -> None:
    Event(
        id="2020nyny",
        event_short="nyny",
        year=2020,
        name="Test Event",
        event_type_enum=EventType.OFFSEASON,
        start_date=datetime(2020, 3, 1),
        end_date=datetime(2020, 3, 5),
        webcast_json=json.dumps([{"type": "youtube", "channel": "abc123defgh"}]),
    ).put()

    resp = web_client.get("/admin/event/2020nyny")
    assert resp.status_code == 200
    soup = bs4.BeautifulSoup(resp.data, "html.parser")
    cleanup_buttons = [
        btn
        for btn in soup.find_all("button")
        if "Clean up YouTube webcasts" in btn.get_text()
    ]
    assert len(cleanup_buttons) == 1
