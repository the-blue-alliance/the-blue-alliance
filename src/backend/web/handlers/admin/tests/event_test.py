import json
from datetime import datetime
from typing import Dict
from unittest.mock import patch

import bs4
from freezegun import freeze_time
from google.appengine.ext import ndb
from pyre_extensions import none_throws
from werkzeug.test import Client

from backend.common.consts.comp_level import CompLevel
from backend.common.consts.event_sync_type import EventSyncType
from backend.common.consts.event_type import EventType
from backend.common.consts.playoff_type import PlayoffType
from backend.common.memcache_models.event_sync_status_memcache import (
    EventSyncStatusMemcache,
)
from backend.common.models.district import District
from backend.common.models.event import Event
from backend.common.models.event_details import EventDetails
from backend.common.models.event_team import EventTeam
from backend.common.models.location import Location
from backend.common.models.match import Match
from backend.common.models.nexus_event_details import NexusEventDetails
from backend.common.models.team import Team
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
        data={
            "frc_event_input": "https://frc-events.firstinspires.org/",
            "csrf_token": "test",
        },
    )
    assert resp.status_code == 302
    assert "link_frc_api_error=invalid_url" in resp.headers.get("Location", "")

    event = Event.get_by_id("2026ohnew")
    assert event is not None
    assert event.official is False


def test_link_frc_api_post_invalid_code_redirects_with_error(
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
        data={"frc_event_input": "OH NEW", "csrf_token": "test"},
    )
    assert resp.status_code == 302
    assert "link_frc_api_error=invalid_code" in resp.headers.get("Location", "")

    event = Event.get_by_id("2026ohnew")
    assert event is not None
    assert event.official is False
    assert event.first_code is None


# ---------------------------------------------------------------------------
# Helpers for the tests below
# ---------------------------------------------------------------------------


def _store_match(
    event_key: str, comp_level: CompLevel, match_number: int, played: bool
) -> Match:
    score = 10 if played else -1
    match = Match(
        id=f"{event_key}_{comp_level}{'' if comp_level == CompLevel.QM else '1m'}{match_number}",
        event=ndb.Key(Event, event_key),
        year=int(event_key[:4]),
        comp_level=comp_level,
        set_number=1,
        match_number=match_number,
        team_key_names=["frc1", "frc2", "frc3", "frc4", "frc5", "frc6"],
        alliances_json=json.dumps(
            {
                "red": {"score": score, "teams": ["frc1", "frc2", "frc3"]},
                "blue": {"score": score, "teams": ["frc4", "frc5", "frc6"]},
            }
        ),
    )
    match.put()
    return match


# ---------------------------------------------------------------------------
# /admin/event/<event_key>  (GET) - match stats
# ---------------------------------------------------------------------------


def test_event_detail_match_stats_skip_empty_levels(
    web_client: Client, login_gae_admin
) -> None:
    helpers.preseed_event("2020nyny")
    _store_match("2020nyny", CompLevel.QM, 1, played=True)
    _store_match("2020nyny", CompLevel.QM, 2, played=False)

    resp = web_client.get("/admin/event/2020nyny")
    assert resp.status_code == 200
    soup = bs4.BeautifulSoup(resp.data, "html.parser")
    heading = soup.find("h2", string="Match Stats")
    assert heading is not None
    stats_table = heading.find_next("table")
    assert stats_table is not None
    rows = stats_table.find_all("tr")
    # Header + one row for qualification matches only
    assert len(rows) == 2
    cells = [c.get_text(strip=True) for c in rows[1].find_all("td")]
    assert cells[0].startswith("Qualification")
    assert cells[1:4] == ["2", "1", "1"]


def test_event_detail_district_points_sorted(
    web_client: Client, login_gae_admin
) -> None:
    Event(
        id="2025ctwat",
        event_short="ctwat",
        year=2025,
        name="Test District Event",
        event_type_enum=EventType.DISTRICT,
        district_key=ndb.Key(District, "2025ne"),
        start_date=datetime(2025, 3, 1),
        end_date=datetime(2025, 3, 5),
    ).put()
    EventDetails(
        id="2025ctwat",
        district_points={
            "points": {
                "frc1": {
                    "qual_points": 3,
                    "elim_points": 4,
                    "alliance_points": 5,
                    "award_points": 6,
                    "total": 18,
                },
                "frc2": {
                    "qual_points": 10,
                    "elim_points": 10,
                    "alliance_points": 10,
                    "award_points": 0,
                    "total": 30,
                },
            },
            "tiebreakers": {
                "frc1": {"qual_wins": 0, "highest_match_scores": []},
                "frc2": {"qual_wins": 0, "highest_match_scores": []},
            },
        },
    ).put()

    resp = web_client.get("/admin/event/2025ctwat")
    assert resp.status_code == 200

    soup = bs4.BeautifulSoup(resp.data, "html.parser")
    heading = soup.find("h2", string="District Points")
    assert heading is not None
    table = heading.find_next("table")
    assert table is not None
    rows = table.find_all("tr")[1:]
    teams = [row.find("a").get_text(strip=True) for row in rows]
    # Sorted by total points descending
    assert teams == ["2", "1"]
    totals = [row.find_all("td")[-1].get_text(strip=True) for row in rows]
    assert totals == ["30", "18"]


# ---------------------------------------------------------------------------
# /admin/event/<event_key>/edit  (GET)
# ---------------------------------------------------------------------------


def test_event_edit_get_not_found(web_client: Client, login_gae_admin) -> None:
    resp = web_client.get("/admin/event/2020nyny/edit")
    assert resp.status_code == 404


def test_event_edit_get(web_client: Client, login_gae_admin) -> None:
    helpers.preseed_event("2020nyny")
    EventDetails(
        id="2020nyny",
        alliance_selections=[{"picks": ["frc1", "frc2", "frc3"], "declines": []}],
        rankings=[["Rank", "Team"], [1, "1"]],
    ).put()

    resp = web_client.get("/admin/event/2020nyny/edit")
    assert resp.status_code == 200
    content = resp.data.decode("utf-8")
    assert 'name="event_short" value="nyny"' in content
    assert "frc1" in content
    assert "sync_disabled::EVENT_ALLIANCES" in content


# ---------------------------------------------------------------------------
# /admin/event/create
# ---------------------------------------------------------------------------


def test_event_create_get(web_client: Client, login_gae_admin) -> None:
    resp = web_client.get("/admin/event/create")
    assert resp.status_code == 200
    soup = bs4.BeautifulSoup(resp.data, "html.parser")
    form = soup.find("form", method="post")
    assert form is not None
    assert form["action"].startswith("/admin/event/edit")
    assert form.find("input", attrs={"name": "event_short"}) is not None
    assert form.find("select", attrs={"name": "event_type"}) is not None


# ---------------------------------------------------------------------------
# /admin/event/<event_key>/delete
# ---------------------------------------------------------------------------


def test_event_delete_get_not_found(web_client: Client, login_gae_admin) -> None:
    resp = web_client.get("/admin/event/2020nyny/delete")
    assert resp.status_code == 404


def test_event_delete_get(web_client: Client, login_gae_admin) -> None:
    helpers.preseed_event("2020nyny")
    resp = web_client.get("/admin/event/2020nyny/delete")
    assert resp.status_code == 200
    assert b"Delete 2020nyny?" in resp.data


def test_event_delete_post_not_found(
    web_client: Client, login_gae_admin, taskqueue_stub
) -> None:
    resp = web_client.post("/admin/event/2020nyny/delete")
    assert resp.status_code == 404


def test_event_delete_post_removes_event_matches_and_eventteams(
    web_client: Client, login_gae_admin, taskqueue_stub
) -> None:
    helpers.preseed_event("2020nyny")
    helpers.preseed_event("2020casj")
    _store_match("2020nyny", CompLevel.QM, 1, played=True)
    _store_match("2020casj", CompLevel.QM, 1, played=True)
    EventTeam(
        id="2020nyny_frc1",
        event=ndb.Key(Event, "2020nyny"),
        team=ndb.Key(Team, "frc1"),
        year=2020,
    ).put()
    EventTeam(
        id="2020casj_frc1",
        event=ndb.Key(Event, "2020casj"),
        team=ndb.Key(Team, "frc1"),
        year=2020,
    ).put()

    resp = web_client.post("/admin/event/2020nyny/delete")
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/admin/events"

    assert Event.get_by_id("2020nyny") is None
    assert Match.get_by_id("2020nyny_qm1") is None
    assert EventTeam.get_by_id("2020nyny_frc1") is None
    # Other events are untouched
    assert Event.get_by_id("2020casj") is not None
    assert Match.get_by_id("2020casj_qm1") is not None
    assert EventTeam.get_by_id("2020casj_frc1") is not None


# ---------------------------------------------------------------------------
# /admin/event/delete_matches/<event_key>/<comp_level>/<to_delete>
# ---------------------------------------------------------------------------


def test_event_delete_matches_invalid_key(web_client: Client, login_gae_admin) -> None:
    resp = web_client.get("/admin/event/delete_matches/asdf/qm/all")
    assert resp.status_code == 404


def test_event_delete_matches_not_found(web_client: Client, login_gae_admin) -> None:
    resp = web_client.get("/admin/event/delete_matches/2020nyny/qm/all")
    assert resp.status_code == 404


def test_event_delete_matches_bad_comp_level(
    web_client: Client, login_gae_admin
) -> None:
    helpers.preseed_event("2020nyny")
    resp = web_client.get("/admin/event/delete_matches/2020nyny/bogus/all")
    assert resp.status_code == 400


def test_event_delete_matches_all(
    web_client: Client, login_gae_admin, taskqueue_stub
) -> None:
    helpers.preseed_event("2020nyny")
    _store_match("2020nyny", CompLevel.QM, 1, played=True)
    _store_match("2020nyny", CompLevel.QM, 2, played=False)
    _store_match("2020nyny", CompLevel.SF, 1, played=False)

    resp = web_client.get("/admin/event/delete_matches/2020nyny/qm/all")
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/admin/event/2020nyny"

    assert Match.get_by_id("2020nyny_qm1") is None
    assert Match.get_by_id("2020nyny_qm2") is None
    assert Match.get_by_id("2020nyny_sf1m1") is not None


def test_event_delete_matches_unplayed(
    web_client: Client, login_gae_admin, taskqueue_stub
) -> None:
    helpers.preseed_event("2020nyny")
    _store_match("2020nyny", CompLevel.QM, 1, played=True)
    _store_match("2020nyny", CompLevel.QM, 2, played=False)

    resp = web_client.get("/admin/event/delete_matches/2020nyny/qm/unplayed")
    assert resp.status_code == 302

    assert Match.get_by_id("2020nyny_qm1") is not None
    assert Match.get_by_id("2020nyny_qm2") is None


def test_event_delete_matches_unknown_selector_is_noop(
    web_client: Client, login_gae_admin, taskqueue_stub
) -> None:
    helpers.preseed_event("2020nyny")
    _store_match("2020nyny", CompLevel.QM, 1, played=True)

    resp = web_client.get("/admin/event/delete_matches/2020nyny/qm/bogus")
    assert resp.status_code == 302
    assert Match.get_by_id("2020nyny_qm1") is not None


# ---------------------------------------------------------------------------
# /admin/event/edit and /admin/event/<event_key>/edit  (POST)
# ---------------------------------------------------------------------------


def _full_event_form(**overrides) -> Dict[str, str]:
    form = {
        "year": "2020",
        "event_short": "nyny",
        "name": "New York City Regional",
        "short_name": "NYC",
        "start_date": "2020-03-05",
        "end_date": "2020-03-08",
        "first_code": "  nyny  ",
        "event_type": str(int(EventType.REGIONAL)),
        "event_district_key": "2020ne",
        "playoff_type": str(int(PlayoffType.DOUBLE_ELIM_8_TEAM)),
        "venue": "Armory",
        "venue_address": "1 Main St",
        "city": "New York",
        "state_prov": "NY",
        "postalcode": "10001",
        "country": "USA",
        "website": "example.com/nyny",
        "first_eid": "12345",
        "official": "True",
        "enable_predictions": "true",
        "facebook_eid": "fb123",
        "custom_hashtag": "frcnyny",
        "webcast_json": json.dumps([{"type": "twitch", "channel": "nyny"}]),
        "parent_event": "2020cmp",
        "divisions": json.dumps(["2020cmptx", "2020cmpmo"]),
        "manual_attrs_csv": "name, website",
        "sync_disabled::EVENT_ALLIANCES": "on",
        "sync_disabled::EVENT_AWARDS": "on",
    }
    form.update(overrides)
    return form


def test_event_edit_post_creates_event(
    web_client: Client, login_gae_admin, taskqueue_stub
) -> None:
    resp = web_client.post("/admin/event/edit", data=_full_event_form())
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/admin/event/2020nyny"

    event = Event.get_by_id("2020nyny")
    assert event is not None
    assert event.event_short == "nyny"
    assert event.name == "New York City Regional"
    assert event.short_name == "NYC"
    assert event.start_date == datetime(2020, 3, 5)
    assert event.end_date == datetime(2020, 3, 8)
    assert event.first_code == "nyny"
    assert event.event_type_enum == EventType.REGIONAL
    assert event.district_key == ndb.Key(District, "2020ne")
    assert event.playoff_type == PlayoffType.DOUBLE_ELIM_8_TEAM
    assert event.venue == "Armory"
    assert event.venue_address == "1 Main St"
    assert event.city == "New York"
    assert event.state_prov == "NY"
    assert event.postalcode == "10001"
    assert event.country == "USA"
    assert event.website == "http://example.com/nyny"
    assert event.first_eid == "12345"
    assert event.year == 2020
    assert event.official is True
    assert event.enable_predictions is True
    assert event.facebook_eid == "fb123"
    assert event.custom_hashtag == "frcnyny"
    assert event.webcast == [{"type": "twitch", "channel": "nyny"}]
    assert event.parent_event == ndb.Key(Event, "2020cmp")
    assert event.divisions == [
        ndb.Key(Event, "2020cmptx"),
        ndb.Key(Event, "2020cmpmo"),
    ]
    assert event.manual_attrs == ["name", "website"]
    assert event.disable_sync_flags == int(
        EventSyncType.EVENT_ALLIANCES | EventSyncType.EVENT_AWARDS
    )
    assert not event.is_sync_enabled(EventSyncType.EVENT_ALLIANCES)
    assert event.is_sync_enabled(EventSyncType.EVENT_RANKINGS)
    assert EventDetails.get_by_id("2020nyny") is None


def test_event_edit_post_uppercase_event_short(
    web_client: Client, login_gae_admin, taskqueue_stub
) -> None:
    # The key is lowercased, but event_short is stored verbatim, so the
    # redirect (built from Event.key_name) points at an uppercase key that
    # the event detail page will not find.
    resp = web_client.post(
        "/admin/event/edit", data=_full_event_form(event_short="NYNY")
    )
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/admin/event/2020NYNY"

    assert Event.get_by_id("2020NYNY") is None
    event = Event.get_by_id("2020nyny")
    assert event is not None
    assert event.event_short == "NYNY"
    assert event.key_name == "2020NYNY"


def test_event_edit_post_none_placeholders(
    web_client: Client, login_gae_admin, taskqueue_stub
) -> None:
    # The edit form renders "None" for unset fields; these must round-trip to None
    resp = web_client.post(
        "/admin/event/edit",
        data=_full_event_form(
            start_date="",
            end_date="",
            first_code="None",
            event_district_key="None",
            parent_event="None",
            divisions="[]",
            website="None",
            official="false",
            enable_predictions="",
            manual_attrs_csv="",
        ),
    )
    assert resp.status_code == 302

    event = Event.get_by_id("2020nyny")
    assert event is not None
    assert event.start_date is None
    assert event.end_date is None
    assert event.first_code is None
    assert event.district_key is None
    assert event.parent_event is None
    assert event.divisions == []
    assert event.website == "None"
    assert event.official is False
    # An empty string is not in the {"true", "false"} lookup, so it becomes None
    assert event.enable_predictions is None
    assert event.manual_attrs == [""]


def test_event_edit_post_empty_divisions_field_fails(
    web_client: Client, login_gae_admin, taskqueue_stub
) -> None:
    # The divisions field is parsed as JSON, so an empty string (rather than
    # "[]", which the edit form always renders) is rejected before any write.
    resp = web_client.post("/admin/event/edit", data=_full_event_form(divisions=""))
    assert resp.status_code == 500
    assert Event.get_by_id("2020nyny") is None


def test_event_edit_post_defaults_when_fields_missing(
    web_client: Client, login_gae_admin, taskqueue_stub
) -> None:
    resp = web_client.post(
        "/admin/event/edit",
        data={"year": "2020", "event_short": "nyny"},
    )
    assert resp.status_code == 302

    event = Event.get_by_id("2020nyny")
    assert event is not None
    assert event.event_type_enum == EventType.UNLABLED
    assert event.playoff_type == PlayoffType.BRACKET_8_TEAM
    assert event.official is False
    assert event.enable_predictions is False
    assert event.website is None
    assert event.disable_sync_flags == 0


def test_event_edit_post_mismatched_key(
    web_client: Client, login_gae_admin, taskqueue_stub
) -> None:
    helpers.preseed_event("2020nyny")
    resp = web_client.post(
        "/admin/event/2020nyny/edit",
        data=_full_event_form(event_short="casj"),
    )
    assert resp.status_code == 400

    event = Event.get_by_id("2020nyny")
    assert event is not None
    assert event.name == "Test Event"


def test_event_edit_post_updates_existing_event_and_details(
    web_client: Client, login_gae_admin, taskqueue_stub
) -> None:
    helpers.preseed_event("2020nyny")
    alliances = [{"picks": ["frc1", "frc2", "frc3"], "declines": []}]
    rankings = [["Rank", "Team"], [1, "1"]]

    resp = web_client.post(
        "/admin/event/2020nyny/edit",
        data=_full_event_form(
            alliance_selections_json=json.dumps(alliances),
            rankings_json=json.dumps(rankings),
        ),
    )
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/admin/event/2020nyny"

    event = Event.get_by_id("2020nyny")
    assert event is not None
    assert event.name == "New York City Regional"
    assert event.event_type_enum == EventType.REGIONAL

    details = EventDetails.get_by_id("2020nyny")
    assert details is not None
    assert details.alliance_selections == alliances
    assert details.rankings == rankings


def test_event_edit_post_only_rankings_json(
    web_client: Client, login_gae_admin, taskqueue_stub
) -> None:
    helpers.preseed_event("2020nyny")
    rankings = [["Rank", "Team"], [1, "1"]]

    resp = web_client.post(
        "/admin/event/2020nyny/edit",
        data=_full_event_form(rankings_json=json.dumps(rankings)),
    )
    assert resp.status_code == 302

    details = EventDetails.get_by_id("2020nyny")
    assert details is not None
    assert details.alliance_selections == []
    assert details.rankings == rankings


def test_event_edit_post_create_with_details_json_fails(
    web_client: Client, login_gae_admin, taskqueue_stub
) -> None:
    # On the create path (no event_key in the URL) the handler builds
    # EventDetails(id=event_key) with event_key=None instead of the computed
    # key, so the manipulator blows up after the Event itself has been saved.
    alliances = [{"picks": ["frc1", "frc2", "frc3"], "declines": []}]
    resp = web_client.post(
        "/admin/event/edit",
        data=_full_event_form(alliance_selections_json=json.dumps(alliances)),
    )
    assert resp.status_code == 500

    event = Event.get_by_id("2020nyny")
    assert event is not None
    assert event.name == "New York City Regional"
    assert EventDetails.get_by_id("2020nyny") is None


# ---------------------------------------------------------------------------
# /admin/event/<event_key>  (POST)
# ---------------------------------------------------------------------------


def test_event_detail_post_invalid_key(web_client: Client, login_gae_admin) -> None:
    resp = web_client.post("/admin/event/asdf", data={"first_code": "x"})
    assert resp.status_code == 404


def test_event_detail_post_not_found(web_client: Client, login_gae_admin) -> None:
    resp = web_client.post("/admin/event/2020nyny", data={"first_code": "x"})
    assert resp.status_code == 404


def test_event_detail_post_sync_override_flags_set_and_cleared(
    web_client: Client, login_gae_admin, taskqueue_stub
) -> None:
    helpers.preseed_event("2020nyny")

    resp = web_client.post(
        "/admin/event/2020nyny",
        data={
            "event_sync_disable": "on",
            "set_start_day_to_last": "on",
            "skip_eventteams": "on",
        },
    )
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/admin/event/2020nyny"

    event = Event.get_by_id("2020nyny")
    assert event is not None
    assert event.sync_overrides == {
        "event_sync_disable": True,
        "set_start_day_to_last": True,
        "skip_eventteams": True,
    }

    # The detail page reflects the flags as checked
    resp = web_client.get("/admin/event/2020nyny")
    assert resp.status_code == 200
    soup = bs4.BeautifulSoup(resp.data, "html.parser")
    for name in ("event_sync_disable", "set_start_day_to_last", "skip_eventteams"):
        checkbox = soup.find("input", attrs={"name": name})
        assert checkbox is not None
        assert checkbox.has_attr("checked")

    # Submitting the form without the flags clears them
    resp = web_client.post("/admin/event/2020nyny", data={})
    assert resp.status_code == 302

    event = Event.get_by_id("2020nyny")
    assert event is not None
    assert event.sync_overrides == {}


# ---------------------------------------------------------------------------
# /admin/event/remap_teams/<event_key>
# ---------------------------------------------------------------------------


def test_event_remap_teams_not_found(
    web_client: Client, login_gae_admin, taskqueue_stub
) -> None:
    resp = web_client.post(
        "/admin/event/remap_teams/2020nyny",
        data={"remap_teams": json.dumps({"1": "1B"})},
    )
    assert resp.status_code == 404


def test_event_remap_teams(web_client: Client, login_gae_admin, taskqueue_stub) -> None:
    helpers.preseed_event("2020nyny")
    resp = web_client.post(
        "/admin/event/remap_teams/2020nyny",
        data={"remap_teams": json.dumps({"1": "1B", "9999": "254"})},
    )
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/admin/event/2020nyny"

    event = Event.get_by_id("2020nyny")
    assert event is not None
    assert event.remap_teams == {"frc1": "frc1B", "frc9999": "frc254"}

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="admin")
    assert [t.url for t in tasks] == ["/tasks/do/remap_teams/2020nyny"]


def test_event_remap_teams_empty_clears_mapping(
    web_client: Client, login_gae_admin, taskqueue_stub
) -> None:
    helpers.preseed_event("2020nyny")
    event = Event.get_by_id("2020nyny")
    assert event is not None
    event.remap_teams = {"frc1": "frc1B"}
    event.put()

    resp = web_client.post("/admin/event/remap_teams/2020nyny", data={})
    assert resp.status_code == 302

    event = Event.get_by_id("2020nyny")
    assert event is not None
    assert event.remap_teams == {}


# ---------------------------------------------------------------------------
# /admin/event/update_location/<event_key>
# ---------------------------------------------------------------------------


def test_event_update_location_get_not_found(
    web_client: Client, login_gae_admin
) -> None:
    resp = web_client.get("/admin/event/update_location/2020nyny")
    assert resp.status_code == 404


def test_event_update_location_get_without_location(
    web_client: Client, login_gae_admin, taskqueue_stub
) -> None:
    # Events without any city/state/country have nothing to geocode
    helpers.preseed_event("2020nyny")
    resp = web_client.get("/admin/event/update_location/2020nyny")
    assert resp.status_code == 200
    assert resp.data == b"New location: None"


def test_event_update_location_get(
    web_client: Client, login_gae_admin, taskqueue_stub
) -> None:
    Event(
        id="2020nyny",
        event_short="nyny",
        year=2020,
        name="Test Event",
        event_type_enum=EventType.REGIONAL,
        city="New York",
        state_prov="NY",
        country="USA",
        normalized_location=Location(name="Stale"),
    ).put()

    with patch(
        "backend.web.handlers.admin.event.LocationHelper.get_event_location",
        return_value=Location(name="Armory", city="New York", place_id="abc"),
    ) as mock_get_location:
        resp = web_client.get("/admin/event/update_location/2020nyny")

    assert resp.status_code == 200
    assert b"Armory" in resp.data
    mock_get_location.assert_called_once()

    event = Event.get_by_id("2020nyny")
    assert event is not None
    location = none_throws(event.normalized_location)
    assert location.name == "Armory"
    assert location.place_id == "abc"


def test_event_update_location_post_not_found(
    web_client: Client, login_gae_admin
) -> None:
    resp = web_client.post(
        "/admin/event/update_location/2020nyny", data={"place_id": "abc"}
    )
    assert resp.status_code == 404


def test_event_update_location_post_missing_place_id(
    web_client: Client, login_gae_admin
) -> None:
    helpers.preseed_event("2020nyny")
    resp = web_client.post("/admin/event/update_location/2020nyny", data={})
    assert resp.status_code == 400


def test_event_update_location_post(
    web_client: Client, login_gae_admin, taskqueue_stub
) -> None:
    helpers.preseed_event("2020nyny")

    location_info = {
        "place_id": "abc",
        "lat": 40.7,
        "lng": -74.0,
        "name": "Armory",
        "types": [],
        "city": "New York",
        "state_prov": "New York",
        "state_prov_short": "NY",
        "country": "United States",
        "country_short": "US",
    }
    with patch(
        "backend.web.handlers.admin.event.LocationHelper.construct_location_info",
        return_value=location_info,
    ) as mock_construct:
        resp = web_client.post(
            "/admin/event/update_location/2020nyny", data={"place_id": "abc"}
        )

    assert resp.status_code == 302
    assert resp.headers["Location"] == "/admin/event/2020nyny"
    mock_construct.assert_called_once()
    assert mock_construct.call_args[0][0]["place_id"] == "abc"

    event = Event.get_by_id("2020nyny")
    assert event is not None
    location = none_throws(event.normalized_location)
    assert location.name == "Armory"
    assert location.place_id == "abc"
    assert location.city == "New York"
    assert location.state_prov_short == "NY"
    assert location.lat_lng == ndb.GeoPt(40.7, -74.0)


# ---------------------------------------------------------------------------
# /admin/event/add_webcast/<event_key> and /admin/event/remove_webcast/<event_key>
# ---------------------------------------------------------------------------


def test_add_webcast_not_found(web_client: Client, login_gae_admin) -> None:
    resp = web_client.post(
        "/admin/event/add_webcast/2020nyny",
        data={"webcast_url": "https://www.twitch.tv/firstinspires"},
    )
    assert resp.status_code == 404


def test_add_webcast_via_manual_fields_with_file_and_date(
    web_client: Client, login_gae_admin, taskqueue_stub
) -> None:
    helpers.preseed_event("2020nyny")
    resp = web_client.post(
        "/admin/event/add_webcast/2020nyny",
        data={
            "webcast_url": "",
            "webcast_type": "youtube",
            "webcast_channel": "abc123defgh",
            "webcast_file": "somefile",
            "webcast_date": "2020-03-01",
        },
    )
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/admin/event/2020nyny#webcasts"

    event = Event.get_by_id("2020nyny")
    assert event is not None
    assert {
        "type": "youtube",
        "channel": "abc123defgh",
        "file": "somefile",
        "date": "2020-03-01",
    } in event.webcast


def test_remove_webcast_not_found(web_client: Client, login_gae_admin) -> None:
    resp = web_client.post(
        "/admin/event/remove_webcast/2020nyny",
        data={"type": "twitch", "channel": "robosportsnetwork", "index": "1"},
    )
    assert resp.status_code == 404


def test_remove_webcast(web_client: Client, login_gae_admin, taskqueue_stub) -> None:
    helpers.preseed_event("2020nyny")
    event = Event.get_by_id("2020nyny")
    assert event is not None
    assert [w["channel"] for w in event.webcast] == [
        "firstinspires",
        "robosportsnetwork",
    ]

    resp = web_client.post(
        "/admin/event/remove_webcast/2020nyny",
        data={"type": "twitch", "channel": "robosportsnetwork", "index": "2"},
    )
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/admin/event/2020nyny#webcasts"

    event = Event.get_by_id("2020nyny")
    assert event is not None
    assert event.webcast == [{"type": "twitch", "channel": "firstinspires"}]


def test_remove_webcast_with_file(
    web_client: Client, login_gae_admin, taskqueue_stub
) -> None:
    Event(
        id="2020nyny",
        event_short="nyny",
        year=2020,
        event_type_enum=EventType.OFFSEASON,
        webcast_json=json.dumps(
            [
                {"type": "youtube", "channel": "abc123defgh", "file": "day1"},
                {"type": "twitch", "channel": "firstinspires"},
            ]
        ),
    ).put()

    resp = web_client.post(
        "/admin/event/remove_webcast/2020nyny",
        data={
            "type": "youtube",
            "channel": "abc123defgh",
            "file": "day1",
            "index": "2",
        },
    )
    assert resp.status_code == 302

    event = Event.get_by_id("2020nyny")
    assert event is not None
    assert event.webcast == [{"type": "twitch", "channel": "firstinspires"}]


def test_remove_webcast_mismatch_is_noop(
    web_client: Client, login_gae_admin, taskqueue_stub
) -> None:
    helpers.preseed_event("2020nyny")

    resp = web_client.post(
        "/admin/event/remove_webcast/2020nyny",
        data={"type": "twitch", "channel": "someoneelse", "index": "1"},
    )
    assert resp.status_code == 302

    event = Event.get_by_id("2020nyny")
    assert event is not None
    assert len(event.webcast) == 2


# ---------------------------------------------------------------------------
# /admin/event/update_webcast_date/<event_key>
# ---------------------------------------------------------------------------


def test_update_webcast_date_index_out_of_range(
    web_client: Client, login_gae_admin
) -> None:
    Event(
        id="2020nyny",
        event_short="nyny",
        year=2020,
        event_type_enum=EventType.OFFSEASON,
        webcast_json=json.dumps([{"type": "youtube", "channel": "abc123defgh"}]),
    ).put()

    resp = web_client.post(
        "/admin/event/update_webcast_date/2020nyny",
        data={"type": "youtube", "channel": "abc123defgh", "index": "2"},
    )
    assert resp.status_code == 400


def test_update_webcast_date_channel_mismatch(
    web_client: Client, login_gae_admin
) -> None:
    Event(
        id="2020nyny",
        event_short="nyny",
        year=2020,
        event_type_enum=EventType.OFFSEASON,
        webcast_json=json.dumps([{"type": "youtube", "channel": "abc123defgh"}]),
    ).put()

    resp = web_client.post(
        "/admin/event/update_webcast_date/2020nyny",
        data={"type": "youtube", "channel": "otherchannel", "index": "1"},
    )
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# /admin/event/update_all_webcast_dates/<event_key>
# ---------------------------------------------------------------------------


def test_update_all_webcast_dates_not_found(
    web_client: Client, login_gae_admin
) -> None:
    resp = web_client.post("/admin/event/update_all_webcast_dates/2020nyny")
    assert resp.status_code == 404


def test_update_all_webcast_dates_no_youtube_webcasts(
    web_client: Client, login_gae_admin
) -> None:
    helpers.preseed_event("2020nyny")

    with patch(
        "backend.web.handlers.admin.event.YouTubeVideoHelper.get_scheduled_start_times"
    ) as mock_get_dates:
        resp = web_client.post("/admin/event/update_all_webcast_dates/2020nyny")

    assert resp.status_code == 302
    assert resp.headers["Location"] == "/admin/event/2020nyny#webcasts"
    mock_get_dates.assert_not_called()


def test_update_all_webcast_dates_skips_non_youtube_and_unchanged(
    web_client: Client, login_gae_admin, taskqueue_stub
) -> None:
    Event(
        id="2020nyny",
        event_short="nyny",
        year=2020,
        event_type_enum=EventType.OFFSEASON,
        webcast_json=json.dumps(
            [
                {"type": "twitch", "channel": "firstinspires"},
                {"type": "youtube", "channel": "abc123defgh", "date": "2020-03-01"},
                {"type": "youtube", "channel": ""},
                {"type": "youtube", "channel": "nodate12345"},
            ]
        ),
    ).put()

    with patch(
        "backend.web.handlers.admin.event.YouTubeVideoHelper.get_scheduled_start_times"
    ) as mock_get_dates:
        mock_future = ndb.Future()
        mock_future.set_result({"abc123defgh": "2020-03-01"})
        mock_get_dates.return_value = mock_future

        resp = web_client.post("/admin/event/update_all_webcast_dates/2020nyny")

    assert resp.status_code == 302
    mock_get_dates.assert_called_once_with(["abc123defgh", "", "nodate12345"])

    # Nothing changed, so the event was not rewritten
    event = Event.get_by_id("2020nyny")
    assert event is not None
    assert len(event.webcast) == 4
    youtube = [w for w in event.webcast if w["type"] == "youtube"]
    assert [w.get("date") for w in youtube] == ["2020-03-01", None, None]


# ---------------------------------------------------------------------------
# /admin/event/link_frc_api/<event_key>
# ---------------------------------------------------------------------------


def test_link_frc_api_post_invalid_key(web_client: Client, login_gae_admin) -> None:
    resp = web_client.post(
        "/admin/event/link_frc_api/asdf", data={"frc_event_input": "NYNY"}
    )
    assert resp.status_code == 404


def test_link_frc_api_post_not_found(web_client: Client, login_gae_admin) -> None:
    resp = web_client.post(
        "/admin/event/link_frc_api/2020nyny", data={"frc_event_input": "NYNY"}
    )
    assert resp.status_code == 404
