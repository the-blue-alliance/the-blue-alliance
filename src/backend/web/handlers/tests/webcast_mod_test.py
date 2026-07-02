import json
from datetime import datetime, timedelta
from unittest import mock
from urllib.parse import parse_qs, urlparse

import pytest
from bs4 import BeautifulSoup
from pyre_extensions import none_throws
from werkzeug.test import Client

from backend.common.consts.account_permission import AccountPermission
from backend.common.consts.event_type import EventType
from backend.common.consts.webcast_status import WebcastStatus
from backend.common.consts.webcast_type import WebcastType
from backend.common.memcache_models.webcast_online_status_memcache import (
    WebcastOnlineStatusMemcache,
)
from backend.common.models.audit_log_entry import AuditLogEntry
from backend.common.models.event import Event
from backend.common.models.event_team import EventTeam
from backend.common.models.match import Match
from backend.common.models.team import Team
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

    offseason_unlinked = Event(
        id=f"{now.year}ohnew",
        name="Ohio Offseason",
        event_short="ohnew",
        short_name="OHNEW",
        year=now.year,
        start_date=now + timedelta(days=20),
        end_date=now + timedelta(days=22),
        timezone_id="America/New_York",
        city="Columbus",
        state_prov="OH",
        country="USA",
        venue="Venue",
        venue_address="101 Main St",
        event_type_enum=EventType.OFFSEASON,
        official=False,
    )
    offseason_unlinked.put()

    offseason_linked = Event(
        id=f"{now.year}caoff",
        name="California Offseason",
        event_short="caoff",
        short_name="CAOFF",
        year=now.year,
        start_date=now + timedelta(days=10),
        end_date=now + timedelta(days=11),
        timezone_id="America/Los_Angeles",
        city="San Jose",
        state_prov="CA",
        country="USA",
        venue="Venue",
        venue_address="202 Main St",
        event_type_enum=EventType.OFFSEASON,
        official=True,
        first_code="CAOFF",
    )
    offseason_linked.put()

    offseason_started = Event(
        id=f"{now.year}pastoff",
        name="Past Offseason",
        event_short="pastoff",
        short_name="PASTOFF",
        year=now.year,
        start_date=now - timedelta(days=2),
        end_date=now + timedelta(days=1),
        timezone_id="America/Los_Angeles",
        city="Oakland",
        state_prov="CA",
        country="USA",
        venue="Venue",
        venue_address="404 Main St",
        event_type_enum=EventType.OFFSEASON,
        official=False,
    )
    offseason_started.put()

    offseason_old_year = Event(
        id=f"{now.year - 1}oldoff",
        name="Old Year Offseason",
        event_short="oldoff",
        short_name="OLDOFF",
        year=now.year - 1,
        start_date=now + timedelta(days=10),
        end_date=now + timedelta(days=11),
        timezone_id="America/Los_Angeles",
        city="Los Angeles",
        state_prov="CA",
        country="USA",
        venue="Venue",
        venue_address="303 Main St",
        event_type_enum=EventType.OFFSEASON,
        official=False,
    )
    offseason_old_year.put()

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


@pytest.fixture
def login_user_with_offseason_permission(login_user):
    login_user.permissions = [AccountPermission.REVIEW_OFFSEASON_EVENTS]
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

    update_all_dates_buttons = [
        btn for btn in soup.find_all("button") if "Update All Dates" in btn.get_text()
    ]
    assert len(update_all_dates_buttons) == 1


@mock.patch(
    "backend.web.handlers.webcast_mod.YouTubeVideoHelper.get_scheduled_start_times"
)
def test_add_webcast_from_url_autofills_youtube_date(
    mock_get_scheduled_start_times,
    login_user_with_permission,
    web_client: Client,
    taskqueue_stub,
) -> None:
    event_key = f"{datetime.now().year}casj"
    mock_get_scheduled_start_times.return_value.get_result.return_value = {
        "xyz987": "2026-03-28"
    }

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
    assert parse_qs(parsed.query)["status"] == ["invalid_webcast_url"]


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
            "csrf_token": "ignore-me",
        },
    )

    assert response.status_code == 302
    event = Event.get_by_id(event_key)
    assert event is not None
    webcasts = event.webcast or []
    assert len(webcasts) == 1
    assert webcasts[0]["channel"] == "abc123"


def test_update_webcast_date_success(
    login_user_with_permission, web_client: Client, taskqueue_stub
) -> None:
    event_key = f"{datetime.now().year}casj"
    response = web_client.post(
        f"/mod/webcast/{event_key}/update_date",
        data={
            "index": "1",
            "type": "youtube",
            "channel": "abc123",
            "file": "",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "csrf_token": "ignore-me",
        },
    )

    assert response.status_code == 302
    event = Event.get_by_id(event_key)
    assert event is not None
    youtube_webcasts = [w for w in event.webcast if w["type"] == "youtube"]
    assert len(youtube_webcasts) == 1
    assert youtube_webcasts[0]["date"] == datetime.now().strftime("%Y-%m-%d")


def test_update_webcast_date_invalid_format(
    login_user_with_permission, web_client: Client
) -> None:
    event_key = f"{datetime.now().year}casj"
    response = web_client.post(
        f"/mod/webcast/{event_key}/update_date",
        data={
            "index": "1",
            "type": "youtube",
            "channel": "abc123",
            "file": "",
            "date": "03/01/2026",
            "csrf_token": "ignore-me",
        },
    )

    assert response.status_code == 302
    parsed = urlparse(response.headers["Location"])
    assert parsed.path == f"/mod/webcast/{event_key}"
    assert parse_qs(parsed.query)["status"] == ["invalid_webcast_date_format"]


def test_update_webcast_date_out_of_event_range(
    login_user_with_permission, web_client: Client
) -> None:
    event_key = f"{datetime.now().year}casj"
    response = web_client.post(
        f"/mod/webcast/{event_key}/update_date",
        data={
            "index": "1",
            "type": "youtube",
            "channel": "abc123",
            "file": "",
            "date": (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d"),
            "csrf_token": "ignore-me",
        },
    )

    assert response.status_code == 302
    parsed = urlparse(response.headers["Location"])
    assert parsed.path == f"/mod/webcast/{event_key}"
    assert parse_qs(parsed.query)["status"] == ["webcast_date_out_of_range"]


def test_webcast_detail_renders_status_error_message(
    login_user_with_permission, web_client: Client
) -> None:
    event_key = f"{datetime.now().year}casj"

    response = web_client.get(
        f"/mod/webcast/{event_key}?status=invalid_webcast_date_format"
    )

    assert response.status_code == 200
    soup = BeautifulSoup(response.data, "html.parser")
    status_message = soup.find(id="webcast-status-message")
    assert status_message is not None
    assert "Webcast date must be in YYYY-MM-DD format." in status_message.get_text()


@mock.patch(
    "backend.web.handlers.webcast_mod.YouTubeVideoHelper.get_scheduled_start_times"
)
def test_update_all_webcast_dates_success(
    mock_get_scheduled_start_times,
    login_user_with_permission,
    web_client: Client,
    taskqueue_stub,
) -> None:
    event_key = f"{datetime.now().year}casj"
    mock_get_scheduled_start_times.return_value.get_result.return_value = {
        "abc123": datetime.now().strftime("%Y-%m-%d"),
    }

    response = web_client.post(
        f"/mod/webcast/{event_key}/update_all_dates",
        data={"csrf_token": "ignore-me"},
    )

    assert response.status_code == 302
    event = Event.get_by_id(event_key)
    assert event is not None
    youtube_webcasts = [w for w in event.webcast if w["type"] == "youtube"]
    assert len(youtube_webcasts) == 1
    assert youtube_webcasts[0]["date"] == datetime.now().strftime("%Y-%m-%d")


def test_remove_webcast_creates_audit_log(
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

    entries = AuditLogEntry.query().fetch()
    assert len(entries) == 1

    entry = entries[0]
    assert entry.account == login_user_with_permission.account_key
    assert entry.endpoint == "webcast_mod.webcast_remove"
    assert entry.target_key is not None
    assert entry.target_key.kind() == "Event"
    assert entry.target_key.id() == event_key
    assert entry.url_args == {"event_key": event_key}
    assert entry.form_params == {
        "index": ["2"],
        "type": ["twitch"],
        "channel": ["frc0"],
    }


def test_remove_webcast_bad_request_redirects_with_status_and_audits(
    login_user_with_permission, web_client: Client
) -> None:
    event_key = f"{datetime.now().year}casj"

    response = web_client.post(
        f"/mod/webcast/{event_key}/remove",
        data={
            "index": "2",
            "type": "twitch",
        },
    )

    assert response.status_code == 302
    parsed = urlparse(response.headers["Location"])
    assert parsed.path == f"/mod/webcast/{event_key}"
    assert parse_qs(parsed.query)["status"] == ["missing_webcast_channel"]
    assert AuditLogEntry.query().count() == 1


def test_post_requires_permission(login_user, web_client: Client) -> None:
    event_key = f"{datetime.now().year}casj"

    response = web_client.post(
        f"/mod/webcast/{event_key}/remove",
        data={"index": "1", "type": "twitch", "channel": "frc0"},
    )

    assert response.status_code == 401


def test_offseason_list_login_redirect(web_client: Client) -> None:
    response = web_client.get("/mod/offseasons")

    assert response.status_code == 302
    assert urlparse(response.headers["Location"]).path == "/account/login"


def test_offseason_list_requires_permission(login_user, web_client: Client) -> None:
    response = web_client.get("/mod/offseasons")

    assert response.status_code == 401


def test_offseason_list_shows_current_year_events(
    login_user_with_offseason_permission, web_client: Client
) -> None:
    response = web_client.get("/mod/offseasons")

    assert response.status_code == 200
    soup = BeautifulSoup(response.data, "html.parser")
    events_table = soup.find(id="offseason-events")
    assert events_table is not None
    assert "Ohio Offseason" in events_table.get_text()
    assert "California Offseason" in events_table.get_text()
    assert "Old Year Offseason" not in events_table.get_text()

    linked_input = soup.find("input", id=f"first-code-{datetime.now().year}caoff")
    assert linked_input is not None
    assert linked_input.get("disabled") is not None
    assert soup.find("button", id=f"unlink-{datetime.now().year}caoff") is not None

    unlinked_input = soup.find("input", id=f"first-code-{datetime.now().year}ohnew")
    assert unlinked_input is not None
    assert unlinked_input.get("disabled") is None
    assert soup.find("button", id=f"unlink-{datetime.now().year}ohnew") is None
    future_delete = soup.find("button", id=f"delete-{datetime.now().year}ohnew")
    assert future_delete is not None
    assert future_delete.get("disabled") is None

    started_delete = soup.find("button", id=f"delete-{datetime.now().year}pastoff")
    assert started_delete is not None
    assert started_delete.get("disabled") is not None


def test_offseason_link_with_code(
    login_user_with_offseason_permission, web_client: Client, taskqueue_stub
) -> None:
    event_key = f"{datetime.now().year}ohnew"
    response = web_client.post(
        f"/mod/offseason/{event_key}/link",
        data={"first_code": "ohnew", "csrf_token": "ignore-me"},
    )

    assert response.status_code == 302
    event = Event.get_by_id(event_key)
    assert event is not None
    assert event.official is True
    assert event.first_code == "OHNEW"

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="datafeed")
    assert any(
        t.url == f"/backend-tasks/enqueue/event_details/{event_key}" for t in tasks
    )


def test_offseason_link_with_frc_events_url(
    login_user_with_offseason_permission, web_client: Client, taskqueue_stub
) -> None:
    event_key = f"{datetime.now().year}ohnew"
    response = web_client.post(
        f"/mod/offseason/{event_key}/link",
        data={
            "first_code": f"https://frc-events.firstinspires.org/{datetime.now().year}/OHNEW",
            "csrf_token": "ignore-me",
        },
    )

    assert response.status_code == 302
    event = Event.get_by_id(event_key)
    assert event is not None
    assert event.first_code == "OHNEW"


def test_offseason_link_invalid_code_redirects_error(
    login_user_with_offseason_permission, web_client: Client
) -> None:
    event_key = f"{datetime.now().year}ohnew"
    response = web_client.post(
        f"/mod/offseason/{event_key}/link",
        data={"first_code": "bad code", "csrf_token": "ignore-me"},
    )

    assert response.status_code == 302
    parsed = urlparse(response.headers["Location"])
    assert parsed.path == "/mod/offseasons"
    assert parse_qs(parsed.query)["status"] == ["invalid_first_code"]


def test_offseason_link_when_already_linked(
    login_user_with_offseason_permission, web_client: Client
) -> None:
    event_key = f"{datetime.now().year}caoff"
    response = web_client.post(
        f"/mod/offseason/{event_key}/link",
        data={"first_code": "CAOFF", "csrf_token": "ignore-me"},
    )

    assert response.status_code == 302
    parsed = urlparse(response.headers["Location"])
    assert parsed.path == "/mod/offseasons"
    assert parse_qs(parsed.query)["status"] == ["already_linked"]


def test_offseason_unlink(
    login_user_with_offseason_permission, web_client: Client, taskqueue_stub
) -> None:
    event_key = f"{datetime.now().year}caoff"

    response = web_client.post(
        f"/mod/offseason/{event_key}/unlink",
        data={"csrf_token": "ignore-me"},
    )

    assert response.status_code == 302
    parsed = urlparse(response.headers["Location"])
    assert parsed.path == "/mod/offseasons"
    assert parse_qs(parsed.query)["status"] == ["unlinked"]

    event = Event.get_by_id(event_key)
    assert event is not None
    assert event.first_code is None
    assert event.official is False


def test_offseason_unlink_when_not_linked(
    login_user_with_offseason_permission, web_client: Client
) -> None:
    event_key = f"{datetime.now().year}ohnew"

    response = web_client.post(
        f"/mod/offseason/{event_key}/unlink",
        data={"csrf_token": "ignore-me"},
    )

    assert response.status_code == 302
    parsed = urlparse(response.headers["Location"])
    assert parsed.path == "/mod/offseasons"
    assert parse_qs(parsed.query)["status"] == ["not_linked"]


def test_offseason_delete(
    login_user_with_offseason_permission, web_client: Client, taskqueue_stub
) -> None:
    event_key = f"{datetime.now().year}ohnew"
    event = Event.get_by_id(event_key)
    assert event is not None

    Team(id="frc1", team_number=1, nickname="Team 1").put()
    Match(
        id=f"{event_key}_qm1",
        event=event.key,
        year=event.year,
        comp_level="qm",
        set_number=1,
        match_number=1,
        team_key_names=["frc1"],
        alliances_json=json.dumps(
            {
                "red": {"teams": ["frc1"], "surrogates": [], "dqs": [], "score": -1},
                "blue": {"teams": [], "surrogates": [], "dqs": [], "score": -1},
            }
        ),
    ).put()
    EventTeam(
        id=f"{event_key}_frc1",
        event=event.key,
        team=none_throws(Team.get_by_id("frc1")).key,
        year=event.year,
    ).put()

    response = web_client.post(
        f"/mod/offseason/{event_key}/delete",
        data={"csrf_token": "ignore-me"},
    )

    assert response.status_code == 302
    parsed = urlparse(response.headers["Location"])
    assert parsed.path == "/mod/offseasons"
    assert parse_qs(parsed.query)["status"] == ["deleted"]

    assert Event.get_by_id(event_key) is None
    assert Match.get_by_id(f"{event_key}_qm1") is None
    assert EventTeam.get_by_id(f"{event_key}_frc1") is None


def test_offseason_delete_not_allowed_after_start(
    login_user_with_offseason_permission, web_client: Client
) -> None:
    event_key = f"{datetime.now().year}pastoff"

    response = web_client.post(
        f"/mod/offseason/{event_key}/delete",
        data={"csrf_token": "ignore-me"},
    )

    assert response.status_code == 302
    parsed = urlparse(response.headers["Location"])
    assert parsed.path == "/mod/offseasons"
    assert parse_qs(parsed.query)["status"] == ["delete_not_allowed"]
    assert Event.get_by_id(event_key) is not None
