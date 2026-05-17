import json
from datetime import datetime
from unittest.mock import patch

import bs4
from freezegun import freeze_time
from google.appengine.ext import ndb
from werkzeug.test import Client

from backend.common.consts.event_type import EventType
from backend.common.memcache_models.event_sync_status_memcache import (
    EventSyncStatusMemcache,
)
from backend.common.models.event import Event
from backend.common.models.event_details import EventDetails
from backend.common.models.nexus_event_details import NexusEventDetails
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

    soup = bs4.BeautifulSoup(resp.data, "html.parser")
    audit_logs_link = soup.find("a", href="/admin/audit_logs?key=Event:2019nyny")
    assert audit_logs_link is not None


def test_event_detail_teams_subtabs_show_nexus_event_details(
    web_client: Client, login_gae_admin
) -> None:
    Event(
        id="2026casj",
        event_short="casj",
        year=2026,
        name="Test Event",
        event_type_enum=EventType.REGIONAL,
        start_date=datetime(2026, 3, 1),
        end_date=datetime(2026, 3, 5),
    ).put()
    NexusEventDetails(
        id="2026casj",
        pitmap_json={"size": {"x": 100, "y": 50}, "pits": {}},
    ).put()

    resp = web_client.get("/admin/event/2026casj")
    assert resp.status_code == 200

    soup = bs4.BeautifulSoup(resp.data, "html.parser")
    team_list_subtab = soup.find("a", href="#teams-list")
    pit_map_subtab = soup.find("a", href="#teams-pit-map")

    assert team_list_subtab is not None
    assert team_list_subtab.get_text(strip=True) == "Team List"
    assert pit_map_subtab is not None
    assert pit_map_subtab.get_text(strip=True) == "Nexus Pit Map"

    pit_map_pane = soup.find("div", id="teams-pit-map")
    assert pit_map_pane is not None
    pane_text = pit_map_pane.get_text()
    assert "size" in pane_text
    assert "100" in pane_text


def test_event_detail_regional_champs_points_tab_and_task(
    web_client: Client, login_gae_admin
) -> None:
    Event(
        id="2025nyny",
        event_short="nyny",
        year=2025,
        name="Test Event",
        event_type_enum=EventType.REGIONAL,
        start_date=datetime(2025, 3, 1),
        end_date=datetime(2025, 3, 5),
    ).put()
    EventDetails(
        id="2025nyny",
        regional_champs_pool_points={
            "points": {
                "frc1": {
                    "qual_points": 3,
                    "elim_points": 4,
                    "alliance_points": 5,
                    "award_points": 6,
                    "rookie_bonus": 10,
                    "total": 28,
                }
            },
            "tiebreakers": {"frc1": {"qual_wins": 0, "highest_match_scores": []}},
        },
    ).put()

    resp = web_client.get("/admin/event/2025nyny")
    assert resp.status_code == 200

    soup = bs4.BeautifulSoup(resp.data, "html.parser")
    points_tab = soup.find("a", href="#district-points")
    assert points_tab is not None
    assert points_tab.get_text(strip=True) == "Regional Champs Points"

    recompute_ra_points_button = soup.find(
        "a", href="/tasks/math/do/regional_champs_pool_points_calc/2025nyny"
    )
    assert recompute_ra_points_button is not None

    assert soup.find("th", string="Rookie Bonus") is not None
    assert soup.find("td", string="10") is not None


def test_event_detail_non_eligible_regional_points_tab_and_task(
    web_client: Client, login_gae_admin
) -> None:
    Event(
        id="2024nyny",
        event_short="nyny",
        year=2024,
        name="Test Event",
        event_type_enum=EventType.REGIONAL,
        start_date=datetime(2024, 3, 1),
        end_date=datetime(2024, 3, 5),
    ).put()

    resp = web_client.get("/admin/event/2024nyny")
    assert resp.status_code == 200

    soup = bs4.BeautifulSoup(resp.data, "html.parser")
    points_tab = soup.find("a", href="#district-points")
    assert points_tab is not None
    assert points_tab.get_text(strip=True) == "District Points"

    recompute_ra_points_button = soup.find(
        "a", href="/tasks/math/do/regional_champs_pool_points_calc/2024nyny"
    )
    assert recompute_ra_points_button is None


def test_event_detail_sync_status_tab_and_data(
    web_client: Client, login_gae_admin
) -> None:
    Event(
        id="2025nyny",
        event_short="nyny",
        year=2025,
        name="Test Event",
        event_type_enum=EventType.REGIONAL,
        start_date=datetime(2025, 3, 1),
        end_date=datetime(2025, 3, 5),
    ).put()

    EventSyncStatusMemcache("2025nyny").put(
        {
            "tasks.get.fmsapi_matches": {
                "last_success_time": "2026-03-28T12:34:56+00:00",
                "num_consecutive_failures": 2,
            }
        }
    )

    resp = web_client.get("/admin/event/2025nyny")
    assert resp.status_code == 200

    soup = bs4.BeautifulSoup(resp.data, "html.parser")
    sync_tab = soup.find("a", href="#api-sync")
    assert sync_tab is not None
    assert sync_tab.get_text(strip=True) == "API & Sync"

    sync_pane = soup.find("div", id="api-sync")
    assert sync_pane is not None
    assert "tasks.get.fmsapi_matches" in sync_pane.get_text()
    assert "2026-03-28T12:34:56+00:00" in sync_pane.get_text()
    assert "2" in sync_pane.get_text()


def test_event_detail_api_sync_has_code_override_inputs(
    web_client: Client, login_gae_admin
) -> None:
    Event(
        id="2025nyny",
        event_short="nyny",
        year=2025,
        name="Test Event",
        first_code="fmscode",
        nexus_code="nexuscode",
        event_type_enum=EventType.REGIONAL,
        start_date=datetime(2025, 3, 1),
        end_date=datetime(2025, 3, 5),
    ).put()

    resp = web_client.get("/admin/event/2025nyny")
    assert resp.status_code == 200

    soup = bs4.BeautifulSoup(resp.data, "html.parser")
    sync_pane = soup.find("div", id="api-sync")
    assert sync_pane is not None

    first_code_input = sync_pane.find("input", id="first_code")
    assert first_code_input is not None
    assert first_code_input.get("value") == "fmscode"

    nexus_code_input = sync_pane.find("input", id="nexus_code")
    assert nexus_code_input is not None
    assert nexus_code_input.get("value") == "nexuscode"


def test_event_detail_post_updates_api_code_overrides(
    web_client: Client, login_gae_admin, taskqueue_stub
) -> None:
    Event(
        id="2025nyny",
        event_short="nyny",
        year=2025,
        name="Test Event",
        event_type_enum=EventType.REGIONAL,
        start_date=datetime(2025, 3, 1),
        end_date=datetime(2025, 3, 5),
    ).put()

    resp = web_client.post(
        "/admin/event/2025nyny",
        data={
            "first_code": "  firstovr  ",
            "nexus_code": "  nexusovr  ",
            "csrf_token": "test",
        },
    )
    assert resp.status_code == 302

    event = Event.get_by_id("2025nyny")
    assert event is not None
    assert event.first_code == "firstovr"
    assert event.nexus_code == "nexusovr"

    resp = web_client.post(
        "/admin/event/2025nyny",
        data={
            "first_code": "   ",
            "nexus_code": "   ",
            "csrf_token": "test",
        },
    )
    assert resp.status_code == 302

    event = Event.get_by_id("2025nyny")
    assert event is not None
    assert event.first_code is None
    assert event.nexus_code is None


def test_event_detail_api_sync_has_event_name_override_inputs(
    web_client: Client, login_gae_admin
) -> None:
    Event(
        id="2025cmp",
        event_short="cmp",
        year=2025,
        name="FIRST Championship",
        event_type_enum=EventType.CMP_FINALS,
        start_date=datetime(2025, 4, 1),
        end_date=datetime(2025, 4, 5),
        sync_overrides={
            "event_name_override": {
                "name": "Einstein Field",
                "short_name": "Einstein",
            }
        },
    ).put()

    resp = web_client.get("/admin/event/2025cmp")
    assert resp.status_code == 200

    soup = bs4.BeautifulSoup(resp.data, "html.parser")
    sync_pane = soup.find("div", id="api-sync")
    assert sync_pane is not None

    event_name_override_input = sync_pane.find("input", id="event_name_override")
    assert event_name_override_input is not None
    assert event_name_override_input.get("value") == "Einstein Field"

    event_short_name_override_input = sync_pane.find(
        "input", id="event_short_name_override"
    )
    assert event_short_name_override_input is not None
    assert event_short_name_override_input.get("value") == "Einstein"


def test_event_detail_post_updates_event_name_overrides(
    web_client: Client, login_gae_admin, taskqueue_stub
) -> None:
    Event(
        id="2025cmp",
        event_short="cmp",
        year=2025,
        name="FIRST Championship",
        event_type_enum=EventType.CMP_FINALS,
        start_date=datetime(2025, 4, 1),
        end_date=datetime(2025, 4, 5),
    ).put()

    resp = web_client.post(
        "/admin/event/2025cmp",
        data={
            "event_name_override": "Einstein Field",
            "event_short_name_override": "Einstein",
            "csrf_token": "test",
        },
    )
    assert resp.status_code == 302

    event = Event.get_by_id("2025cmp")
    assert event is not None
    assert event.sync_overrides is not None
    assert event.sync_overrides["event_name_override"] == {
        "name": "Einstein Field",
        "short_name": "Einstein",
    }

    resp = web_client.post(
        "/admin/event/2025cmp",
        data={
            "event_name_override": "",
            "event_short_name_override": "",
            "csrf_token": "test",
        },
    )
    assert resp.status_code == 302

    event = Event.get_by_id("2025cmp")
    assert event is not None
    assert event.sync_overrides is not None
    assert "event_name_override" not in event.sync_overrides


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
        "backend.web.handlers.admin.event.YouTubeVideoHelper.get_scheduled_start_times"
    ) as mock_get_date:
        mock_future = ndb.Future()
        mock_future.set_result({"abc123defgh": "2020-03-01"})
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
        "backend.web.handlers.admin.event.YouTubeVideoHelper.get_scheduled_start_times"
    ) as mock_get_date:
        mock_future = ndb.Future()
        mock_future.set_result({})
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

    update_all_date_buttons = [
        btn for btn in soup.find_all("button") if "Update All Dates" in btn.get_text()
    ]
    assert len(update_all_date_buttons) == 1


def test_update_all_webcast_dates_success(
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
                {"type": "youtube", "channel": "xyz987"},
                {"type": "twitch", "channel": "firstinspires"},
            ]
        ),
    ).put()

    with patch(
        "backend.web.handlers.admin.event.YouTubeVideoHelper.get_scheduled_start_times"
    ) as mock_get_dates:
        mock_future = ndb.Future()
        mock_future.set_result(
            {
                "abc123defgh": "2020-03-01",
                "xyz987": "2020-03-02",
            }
        )
        mock_get_dates.return_value = mock_future

        resp = web_client.post(
            "/admin/event/update_all_webcast_dates/2020nyny",
            data={"csrf_token": "test"},
        )

    assert resp.status_code == 302
    event = Event.get_by_id("2020nyny")
    assert event is not None
    webcasts = event.webcast
    youtube_webcasts = [w for w in webcasts if w["type"] == "youtube"]
    twitch_webcasts = [w for w in webcasts if w["type"] == "twitch"]
    assert len(youtube_webcasts) == 2
    assert len(twitch_webcasts) == 1
    assert any(
        w["channel"] == "abc123defgh" and w["date"] == "2020-03-01"
        for w in youtube_webcasts
    )
    assert any(
        w["channel"] == "xyz987" and w["date"] == "2020-03-02" for w in youtube_webcasts
    )
    assert "date" not in twitch_webcasts[0]


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


def test_cleanup_youtube_webcasts_removes_duplicates(
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
                {"type": "youtube", "channel": "abc123defgh", "date": "2020-01-01"},
                {"type": "youtube", "channel": "abc123defgh", "date": "2020-02-01"},
                {"type": "twitch", "channel": "firstinspires"},
            ]
        ),
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
    twitch_webcasts = [w for w in webcasts if w["type"] == "twitch"]
    assert len(twitch_webcasts) == 1


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


def test_divisions_released_not_found(
    web_client: Client, login_gae_admin, taskqueue_stub
) -> None:
    resp = web_client.post(
        "/admin/event/divisions_released/2020cmptx",
        data={"csrf_token": "test"},
    )
    assert resp.status_code == 404


def test_divisions_released_no_divisions(
    web_client: Client, login_gae_admin, taskqueue_stub
) -> None:
    Event(
        id="2020cmptx",
        event_short="cmptx",
        year=2020,
        event_type_enum=EventType.CMP_FINALS,
    ).put()
    resp = web_client.post(
        "/admin/event/divisions_released/2020cmptx",
        data={"csrf_token": "test"},
    )
    assert resp.status_code == 400


def test_divisions_released_enqueues_tasks(
    web_client: Client, login_gae_admin, taskqueue_stub
) -> None:
    div1 = Event(
        id="2020cmpmo",
        event_short="cmpmo",
        year=2020,
        event_type_enum=EventType.CMP_DIVISION,
    )
    div1.put()
    div2 = Event(
        id="2020cmptx",
        event_short="cmptx",
        year=2020,
        event_type_enum=EventType.CMP_DIVISION,
    )
    div2.put()
    Event(
        id="2020cmp",
        event_short="cmp",
        year=2020,
        event_type_enum=EventType.CMP_FINALS,
        divisions=[div1.key, div2.key],
    ).put()

    resp = web_client.post(
        "/admin/event/divisions_released/2020cmp",
        data={"csrf_token": "test"},
    )
    assert resp.status_code == 302

    # Should have enqueued team fetches for all divisions
    tasks = taskqueue_stub.get_filtered_tasks(queue_names="datafeed")
    task_urls = [t.url for t in tasks]
    assert "/backend-tasks/get/event_details/2020cmpmo" in task_urls
    assert "/backend-tasks/get/event_details/2020cmptx" in task_urls

    # Should have enqueued post_division_tasks
    admin_tasks = taskqueue_stub.get_filtered_tasks(queue_names="admin")
    assert any(
        "/tasks/admin/do/post_division_tasks/2020cmp" in t.url for t in admin_tasks
    )


def test_divisions_released_button_shown_when_has_divisions(
    web_client: Client, login_gae_admin, taskqueue_stub
) -> None:
    div = Event(
        id="2020cmpmo",
        event_short="cmpmo",
        year=2020,
        event_type_enum=EventType.CMP_DIVISION,
        start_date=datetime(2020, 4, 1),
        end_date=datetime(2020, 4, 5),
    )
    div.put()
    Event(
        id="2020cmp",
        event_short="cmp",
        year=2020,
        event_type_enum=EventType.CMP_FINALS,
        divisions=[div.key],
        start_date=datetime(2020, 4, 1),
        end_date=datetime(2020, 4, 5),
    ).put()

    resp = web_client.get("/admin/event/2020cmp")
    assert resp.status_code == 200
    soup = bs4.BeautifulSoup(resp.data, "html.parser")
    buttons = [
        btn for btn in soup.find_all("button") if "Divisions Released" in btn.get_text()
    ]
    assert len(buttons) == 1


def test_divisions_released_button_not_shown_without_divisions(
    web_client: Client, login_gae_admin, taskqueue_stub
) -> None:
    Event(
        id="2020nyny",
        event_short="nyny",
        year=2020,
        event_type_enum=EventType.OFFSEASON,
        start_date=datetime(2020, 3, 1),
        end_date=datetime(2020, 3, 5),
    ).put()

    resp = web_client.get("/admin/event/2020nyny")
    assert resp.status_code == 200
    soup = bs4.BeautifulSoup(resp.data, "html.parser")
    buttons = [
        btn for btn in soup.find_all("button") if "Divisions Released" in btn.get_text()
    ]
    assert len(buttons) == 0


def test_link_frc_api_button_shown_for_offseason_unofficial_event(
    web_client: Client, login_gae_admin
) -> None:
    Event(
        id="2026ohnew",
        event_short="ohnew",
        year=2026,
        name="Ohio New Event",
        event_type_enum=EventType.OFFSEASON,
        official=False,
        start_date=datetime(2026, 9, 1),
        end_date=datetime(2026, 9, 5),
    ).put()

    resp = web_client.get("/admin/event/2026ohnew")
    assert resp.status_code == 200
    soup = bs4.BeautifulSoup(resp.data, "html.parser")
    link_form = soup.find("form", action="/admin/event/link_frc_api/2026ohnew")
    assert link_form is not None
    frc_event_input = link_form.find("input", {"name": "frc_event_input"})
    assert frc_event_input is not None


def test_link_frc_api_button_not_shown_for_official_event(
    web_client: Client, login_gae_admin
) -> None:
    Event(
        id="2026ohnew",
        event_short="ohnew",
        year=2026,
        name="Ohio New Event",
        event_type_enum=EventType.OFFSEASON,
        official=True,
        start_date=datetime(2026, 9, 1),
        end_date=datetime(2026, 9, 5),
    ).put()

    resp = web_client.get("/admin/event/2026ohnew")
    assert resp.status_code == 200
    soup = bs4.BeautifulSoup(resp.data, "html.parser")
    link_form = soup.find("form", action="/admin/event/link_frc_api/2026ohnew")
    assert link_form is None


def test_link_frc_api_button_not_shown_for_non_offseason_event(
    web_client: Client, login_gae_admin
) -> None:
    Event(
        id="2026nyny",
        event_short="nyny",
        year=2026,
        name="New York Regional",
        event_type_enum=EventType.REGIONAL,
        official=False,
        start_date=datetime(2026, 3, 1),
        end_date=datetime(2026, 3, 5),
    ).put()

    resp = web_client.get("/admin/event/2026nyny")
    assert resp.status_code == 200
    soup = bs4.BeautifulSoup(resp.data, "html.parser")
    link_form = soup.find("form", action="/admin/event/link_frc_api/2026nyny")
    assert link_form is None


def test_link_frc_api_post_with_event_code(
    web_client: Client, login_gae_admin, taskqueue_stub
) -> None:
    Event(
        id="2026ohnew",
        event_short="ohnew",
        year=2026,
        name="Ohio New Event",
        event_type_enum=EventType.OFFSEASON,
        official=False,
        start_date=datetime(2026, 9, 1),
        end_date=datetime(2026, 9, 5),
    ).put()

    resp = web_client.post(
        "/admin/event/link_frc_api/2026ohnew",
        data={"frc_event_input": "OHNEW", "csrf_token": "test"},
    )
    assert resp.status_code == 302

    event = Event.get_by_id("2026ohnew")
    assert event is not None
    assert event.official is True
    assert event.first_code == "OHNEW"

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="datafeed")
    assert any("/backend-tasks/get/event_details/2026ohnew" in t.url for t in tasks)


def test_link_frc_api_post_with_frc_events_url(
    web_client: Client, login_gae_admin, taskqueue_stub
) -> None:
    Event(
        id="2026ohnew",
        event_short="ohnew",
        year=2026,
        name="Ohio New Event",
        event_type_enum=EventType.OFFSEASON,
        official=False,
        start_date=datetime(2026, 9, 1),
        end_date=datetime(2026, 9, 5),
    ).put()

    resp = web_client.post(
        "/admin/event/link_frc_api/2026ohnew",
        data={
            "frc_event_input": "https://frc-events.firstinspires.org/2026/OHNEW",
            "csrf_token": "test",
        },
    )
    assert resp.status_code == 302

    event = Event.get_by_id("2026ohnew")
    assert event is not None
    assert event.official is True
    assert event.first_code == "OHNEW"

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="datafeed")
    assert any("/backend-tasks/get/event_details/2026ohnew" in t.url for t in tasks)


def test_link_frc_api_post_lowercase_code_uppercased(
    web_client: Client, login_gae_admin, taskqueue_stub
) -> None:
    Event(
        id="2026ohnew",
        event_short="ohnew",
        year=2026,
        name="Ohio New Event",
        event_type_enum=EventType.OFFSEASON,
        official=False,
        start_date=datetime(2026, 9, 1),
        end_date=datetime(2026, 9, 5),
    ).put()

    resp = web_client.post(
        "/admin/event/link_frc_api/2026ohnew",
        data={"frc_event_input": "ohnew", "csrf_token": "test"},
    )
    assert resp.status_code == 302

    event = Event.get_by_id("2026ohnew")
    assert event is not None
    assert event.first_code == "OHNEW"


def test_link_frc_api_post_rejects_official_event(
    web_client: Client, login_gae_admin, taskqueue_stub
) -> None:
    Event(
        id="2026ohnew",
        event_short="ohnew",
        year=2026,
        name="Ohio New Event",
        event_type_enum=EventType.OFFSEASON,
        official=True,
        start_date=datetime(2026, 9, 1),
        end_date=datetime(2026, 9, 5),
    ).put()

    resp = web_client.post(
        "/admin/event/link_frc_api/2026ohnew",
        data={"frc_event_input": "OHNEW", "csrf_token": "test"},
    )
    assert resp.status_code == 400


def test_link_frc_api_post_rejects_non_offseason_event(
    web_client: Client, login_gae_admin, taskqueue_stub
) -> None:
    Event(
        id="2026nyny",
        event_short="nyny",
        year=2026,
        name="New York Regional",
        event_type_enum=EventType.REGIONAL,
        official=False,
        start_date=datetime(2026, 3, 1),
        end_date=datetime(2026, 3, 5),
    ).put()

    resp = web_client.post(
        "/admin/event/link_frc_api/2026nyny",
        data={"frc_event_input": "NYNY", "csrf_token": "test"},
    )
    assert resp.status_code == 400


def test_link_frc_api_post_rejects_empty_input(
    web_client: Client, login_gae_admin, taskqueue_stub
) -> None:
    Event(
        id="2026ohnew",
        event_short="ohnew",
        year=2026,
        name="Ohio New Event",
        event_type_enum=EventType.OFFSEASON,
        official=False,
        start_date=datetime(2026, 9, 1),
        end_date=datetime(2026, 9, 5),
    ).put()

    resp = web_client.post(
        "/admin/event/link_frc_api/2026ohnew",
        data={"frc_event_input": "   ", "csrf_token": "test"},
    )
    assert resp.status_code == 302
    assert "link_frc_api_error=empty" in resp.headers.get("Location", "")

    # Event should not have been modified
    event = Event.get_by_id("2026ohnew")
    assert event is not None
    assert event.official is False
    assert event.first_code is None


def test_link_frc_api_post_invalid_url_redirects_with_error(
    web_client: Client, login_gae_admin, taskqueue_stub
) -> None:
    Event(
        id="2026ohnew",
        event_short="ohnew",
        year=2026,
        name="Ohio New Event",
        event_type_enum=EventType.OFFSEASON,
        official=False,
        start_date=datetime(2026, 9, 1),
        end_date=datetime(2026, 9, 5),
    ).put()

    # A URL with no path segments after the scheme/host
    resp = web_client.post(
        "/admin/event/link_frc_api/2026ohnew",
        data={"frc_event_input": "https://frc-events.firstinspires.org/", "csrf_token": "test"},
    )
    assert resp.status_code == 302
    assert "link_frc_api_error=invalid_url" in resp.headers.get("Location", "")

    event = Event.get_by_id("2026ohnew")
    assert event is not None
    assert event.official is False
