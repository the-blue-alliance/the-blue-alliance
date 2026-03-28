import json
from datetime import datetime, timedelta
from unittest import mock
from urllib.parse import parse_qs, urlparse

import pytest
from bs4 import BeautifulSoup
from werkzeug.test import Client

from backend.common.consts.account_permission import AccountPermission
from backend.common.consts.event_type import EventType
from backend.common.consts.webcast_status import WebcastStatus
from backend.common.consts.webcast_type import WebcastType
from backend.common.memcache_models.webcast_online_status_memcache import (
    WebcastOnlineStatusMemcache,
)
from backend.common.models.event import Event
from backend.common.models.webcast import Webcast


@pytest.fixture(autouse=True)
def create_events(ndb_stub) -> None:
    now = datetime.now()
    active_event = Event(
        id=f"{now.year}casj",
        name="Silicon Valley Regional",
        event_short="casj",
        short_name="SVR",
        year=now.year,
        start_date=now - timedelta(days=1),
        end_date=now + timedelta(days=1),
        timezone_id="America/Los_Angeles",
        city="San Jose",
        state_prov="CA",
        country="USA",
        venue="Venue",
        venue_address="123 Main St",
        event_type_enum=EventType.REGIONAL,
        official=True,
        website="https://example.com",
        webcast_json=json.dumps(
            [
                {"type": "twitch", "channel": "frc0"},
                {
                    "type": "youtube",
                    "channel": "abc123",
                    "date": now.strftime("%Y-%m-%d"),
                },
            ]
        ),
    )
    active_event.put()

    active_event_no_webcast = Event(
        id=f"{now.year}cada",
        name="No Webcast Open",
        event_short="cada",
        short_name="No Webcast",
        year=now.year,
        start_date=now - timedelta(hours=6),
        end_date=now + timedelta(hours=6),
        timezone_id="America/Los_Angeles",
        city="Davis",
        state_prov="CA",
        country="USA",
        venue="Venue",
        venue_address="456 Main St",
        event_type_enum=EventType.REGIONAL,
        official=True,
        website="https://example.com/2",
        webcast_json="",
    )
    active_event_no_webcast.put()

    inactive_event = Event(
        id=f"{now.year}nyny",
        name="Inactive Event",
        event_short="nyny",
        short_name="Inactive",
        year=now.year,
        start_date=now - timedelta(days=10),
        end_date=now - timedelta(days=8),
        timezone_id="America/New_York",
        city="New York",
        state_prov="NY",
        country="USA",
        venue="Venue",
        venue_address="789 Main St",
        event_type_enum=EventType.REGIONAL,
        official=True,
        website="https://example.com/3",
        webcast_json=json.dumps([{"type": "twitch", "channel": "oldstream"}]),
    )
    inactive_event.put()

    webcast_status = Webcast(
        type=WebcastType.TWITCH,
        channel="frc0",
        status=WebcastStatus.ONLINE,
        stream_title="Field stream",
    )
    WebcastOnlineStatusMemcache(webcast_status).put(webcast_status)


@pytest.fixture
def login_user_with_permission(login_user):
    login_user.permissions = [AccountPermission.REVIEW_MEDIA]
    return login_user


def test_login_redirect(web_client: Client) -> None:
    response = web_client.get("/mod/webcasts")

    assert response.status_code == 302
    assert urlparse(response.headers["Location"]).path == "/account/login"


def test_requires_permission(login_user, web_client: Client) -> None:
    response = web_client.get("/mod/webcasts")

    assert response.status_code == 401


def test_list_shows_active_events_and_status(
    login_user_with_permission, web_client: Client
) -> None:
    response = web_client.get("/mod/webcasts")

    assert response.status_code == 200
    soup = BeautifulSoup(response.data, "html.parser")
    events_table = soup.find(id="active-webcast-events")
    assert events_table is not None
    assert "Silicon Valley Regional" in events_table.get_text()
    assert "No Webcast Open" in events_table.get_text()
    assert "Inactive Event" not in events_table.get_text()
    assert "online" in events_table.get_text()
    assert "frc0" in events_table.get_text()


def test_admin_can_view_detail(login_admin, web_client: Client) -> None:
    event_key = f"{datetime.now().year}casj"

    response = web_client.get(f"/mod/webcast/{event_key}")

    assert response.status_code == 200
    soup = BeautifulSoup(response.data, "html.parser")
    assert soup.find(id="webcast-list") is not None
    assert soup.find(id="add-webcast-form") is not None


@mock.patch(
    "backend.web.handlers.webcast_mod.YouTubeVideoHelper.get_scheduled_start_time"
)
def test_add_webcast_from_url_autofills_youtube_date(
    mock_get_scheduled_start_time,
    login_user_with_permission,
    web_client: Client,
    taskqueue_stub,
) -> None:
    event_key = f"{datetime.now().year}casj"
    mock_get_scheduled_start_time.return_value.get_result.return_value = "2026-03-28"

    response = web_client.post(
        f"/mod/webcast/{event_key}/add",
        data={"webcast_url": "https://www.youtube.com/watch?v=xyz987"},
    )

    assert response.status_code == 302
    event = Event.get_by_id(event_key)
    assert event is not None
    assert Webcast(type=WebcastType.YOUTUBE, channel="xyz987", date="2026-03-28") in (
        event.webcast or []
    )


def test_add_invalid_webcast_url_redirects_with_error(
    login_user_with_permission, web_client: Client
) -> None:
    event_key = f"{datetime.now().year}casj"

    response = web_client.post(
        f"/mod/webcast/{event_key}/add",
        data={"webcast_url": "https://example.com/not-supported"},
    )

    assert response.status_code == 302
    parsed = urlparse(response.headers["Location"])
    assert parsed.path == f"/mod/webcast/{event_key}"
    assert parse_qs(parsed.query)["webcast_url_error"] == ["1"]


def test_remove_webcast(
    login_user_with_permission, web_client: Client, taskqueue_stub
) -> None:
    event_key = f"{datetime.now().year}casj"

    response = web_client.post(
        f"/mod/webcast/{event_key}/remove",
        data={
            "index": "2",
            "type": "twitch",
            "channel": "frc0",
        },
    )

    assert response.status_code == 302
    event = Event.get_by_id(event_key)
    assert event is not None
    webcasts = event.webcast or []
    assert len(webcasts) == 1
    assert webcasts[0]["channel"] == "abc123"


def test_post_requires_permission(login_user, web_client: Client) -> None:
    event_key = f"{datetime.now().year}casj"

    response = web_client.post(
        f"/mod/webcast/{event_key}/remove",
        data={"index": "1", "type": "twitch", "channel": "frc0"},
    )

    assert response.status_code == 401
