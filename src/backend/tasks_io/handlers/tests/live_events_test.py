import datetime
import json
from unittest import mock

from freezegun import freeze_time
from google.appengine.ext import ndb, testbed
from werkzeug.test import Client

from backend.common.consts.event_type import EventType
from backend.common.consts.webcast_type import WebcastType
from backend.common.futures import InstantFuture
from backend.common.helpers.event_helper import EventHelper
from backend.common.helpers.event_team_status_helper import EventTeamStatusHelper
from backend.common.helpers.event_webcast_adder import EventWebcastAdder
from backend.common.helpers.firebase_pusher import FirebasePusher
from backend.common.helpers.playoff_advancement_helper import (
    PlayoffAdvancement,
    PlayoffAdvancementHelper,
)
from backend.common.helpers.season_helper import SeasonHelper
from backend.common.helpers.youtube_video_helper import (
    YouTubeUpcomingStream,
    YouTubeVideoHelper,
)
from backend.common.models.district import District
from backend.common.models.event import Event
from backend.common.models.event_details import EventDetails
from backend.common.models.event_playoff_advancement import EventPlayoffAdvancement
from backend.common.models.event_team import EventTeam
from backend.common.models.event_team_status import EventTeamStatus
from backend.common.models.team import Team
from backend.common.models.webcast import Webcast, WebcastChannel
from backend.tasks_io.helpers.live_event_helper import LiveEventHelper


def set_district_webcast_channels(
    district_abbrev: str, channels: list[WebcastChannel], year: int = 2026
) -> None:
    district_key = District.render_key_name(year, district_abbrev)
    district = District.get_by_id(district_key)
    if district is None:
        district = District(id=district_key, year=year, abbreviation=district_abbrev)
    district.webcast_channels = channels
    district.put()


@mock.patch.object(FirebasePusher, "update_live_events")
def test_update_live_events(update_mock: mock.Mock, tasks_client: Client) -> None:
    resp = tasks_client.get("/tasks/do/update_live_events")
    assert resp.status_code == 200

    update_mock.assert_called_once()


def test_enqueue_eventteam_status_bad_year(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    resp = tasks_client.get("/tasks/math/enqueue/event_team_status/asdf")
    assert resp.status_code == 404


def test_enqueue_eventteam_status_no_events(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    resp = tasks_client.get("/tasks/math/enqueue/event_team_status/2020")
    assert resp.status_code == 200
    assert resp.data == b"Enqueued for: []"

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="default")
    assert len(tasks) == 0


def test_enqueue_eventteam_status_no_output_in_taskqueue(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    resp = tasks_client.get(
        "/tasks/math/enqueue/event_team_status/2020",
        headers={"X-Appengine-Taskname": "test"},
    )
    assert resp.status_code == 200
    assert resp.data == b""

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="default")
    assert len(tasks) == 0


def test_enqueue_eventteam_status(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    Event(
        id="2020test",
        year=2020,
        event_short="test",
        event_type_enum=EventType.REGIONAL,
    ).put()
    resp = tasks_client.get("/tasks/math/enqueue/event_team_status/2020")
    assert resp.status_code == 200
    assert resp.data == b"Enqueued for: ['2020test']"

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="default")
    assert len(tasks) == 1


def test_enqueue_eventteam_status_all(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    resp = tasks_client.get("/tasks/math/enqueue/event_team_status/all")
    assert resp.status_code == 200

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="default")
    assert len(tasks) == len(SeasonHelper.get_valid_years())

    task_urls = {t.url for t in tasks}
    expected_urls = {
        f"/tasks/math/enqueue/event_team_status/{y}"
        for y in SeasonHelper.get_valid_years()
    }
    assert task_urls == expected_urls


def test_do_eventteam_status_not_found(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    resp = tasks_client.get("/tasks/math/do/event_team_status/asdf")
    assert resp.status_code == 404

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="default")
    assert len(tasks) == 0


@mock.patch.object(EventTeamStatusHelper, "generate_team_at_event_status")
def test_do_eventteam_status(
    status_mock: mock.Mock,
    tasks_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:
    Event(
        id="2020test",
        year=2020,
        event_short="test",
        event_type_enum=EventType.REGIONAL,
    ).put()
    EventTeam(
        id="2020test_frc254",
        year=2020,
        event=ndb.Key(Event, "2020test"),
        team=ndb.Key(Team, "frc254"),
    ).put()
    status = EventTeamStatus(
        qual=None,
        playoff=None,
        alliance=None,
        last_match_key=None,
        next_match_key=None,
    )
    status_mock.return_value = status

    resp = tasks_client.get("/tasks/math/do/event_team_status/2020test")
    assert resp.status_code == 200
    assert resp.data == b"Finished calculating event team statuses for: 2020test"

    et = EventTeam.get_by_id("2020test_frc254")
    assert et is not None
    assert et.status == status


def test_enqueue_playoff_advancement_all(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    resp = tasks_client.get("/tasks/math/enqueue/playoff_advancement_update/all")
    assert resp.status_code == 200

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="default")
    assert len(tasks) == len(SeasonHelper.get_valid_years())

    task_urls = {t.url for t in tasks}
    expected_urls = {
        f"/tasks/math/enqueue/playoff_advancement_update/{y}"
        for y in SeasonHelper.get_valid_years()
    }
    assert task_urls == expected_urls


def test_enqueue_playoff_advancement_year(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    Event(
        id="2020test",
        year=2020,
        event_short="test",
        event_type_enum=EventType.REGIONAL,
    ).put()
    resp = tasks_client.get("/tasks/math/enqueue/playoff_advancement_update/2020")
    assert resp.status_code == 200

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="default")
    assert len(tasks) == 1
    assert tasks[0].url == "/tasks/math/do/playoff_advancement_update/2020test"


def test_enqueue_playoff_advancement_no_event(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    resp = tasks_client.get("/tasks/math/do/playoff_advancement_update/asdf")
    assert resp.status_code == 404

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="default")
    assert len(tasks) == 0


def test_enqueue_playoff_advancement(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    Event(
        id="2020test",
        year=2020,
        event_short="test",
        event_type_enum=EventType.REGIONAL,
    ).put()
    resp = tasks_client.get("/tasks/math/enqueue/playoff_advancement_update/2020test")
    assert resp.status_code == 200
    assert resp.data == b"Enqueued playoff advancement calc for 2020test"

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="default")
    assert len(tasks) == 1


def test_calc_playoff_advancement_no_event(tasks_client: Client) -> None:
    resp = tasks_client.get("/tasks/math/do/playoff_advancement_update/asdf")
    assert resp.status_code == 404


@mock.patch.object(PlayoffAdvancementHelper, "generate_playoff_advancement")
def test_calc_playoff_advancement(calc_mock: mock.Mock, tasks_client: Client) -> None:
    Event(
        id="2020test",
        year=2020,
        event_short="test",
        event_type_enum=EventType.REGIONAL,
    ).put()
    advancement = PlayoffAdvancement(
        bracket_table={},
        playoff_advancement={},
        double_elim_matches={},
        playoff_template=None,
    )
    calc_mock.return_value = advancement
    resp = tasks_client.get("/tasks/math/do/playoff_advancement_update/2020test")
    assert resp.status_code == 200
    assert len(resp.data) > 0

    # Make sure we set the EventDetails
    ed = EventDetails.get_by_id("2020test")
    assert ed is not None
    assert ed.playoff_advancement == EventPlayoffAdvancement(
        advancement={},
        bracket={},
    )


@mock.patch.object(FirebasePusher, "update_live_events")
@mock.patch.object(LiveEventHelper, "get_live_events_with_current_webcasts")
@mock.patch.object(EventHelper, "week_events")
def test_update_live_events_enqueues_district_webcast_search(
    week_events_mock: mock.Mock,
    live_events_mock: mock.Mock,
    firebase_mock: mock.Mock,
    tasks_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:
    # Setup district webcast channel configuration
    set_district_webcast_channels(
        "fim",
        [
            WebcastChannel(
                type=WebcastType.YOUTUBE,
                channel="FIRST in Michigan",
                channel_id="UCjX4WSaAFPgM2PYr-6P",
            )
        ],
    )
    set_district_webcast_channels(
        "ne",
        [
            WebcastChannel(
                type=WebcastType.YOUTUBE,
                channel="NE FIRST",
                channel_id="UCkOjF9nNXPRqJmMhd",
            )
        ],
    )

    # Create events for this week
    event_with_webcast = Event(
        id="2026fim1",
        year=2026,
        event_short="fim1",
        event_type_enum=EventType.DISTRICT,
        start_date=datetime.datetime.now(),
        end_date=datetime.datetime.now() + datetime.timedelta(days=1),
        district_key=ndb.Key(District, "2026fim"),
        webcast_json=json.dumps(
            [Webcast(type=WebcastType.YOUTUBE, channel="existing123")]
        ),
    )
    event_with_webcast.put()

    event_without_webcast = Event(
        id="2026fim2",
        year=2026,
        event_short="fim2",
        event_type_enum=EventType.DISTRICT,
        start_date=datetime.datetime.now(),
        end_date=datetime.datetime.now() + datetime.timedelta(days=1),
        district_key=ndb.Key(District, "2026fim"),
    )
    event_without_webcast.put()

    event_without_webcast_ne = Event(
        id="2026ne1",
        year=2026,
        event_short="ne1",
        event_type_enum=EventType.DISTRICT,
        start_date=datetime.datetime.now(),
        end_date=datetime.datetime.now() + datetime.timedelta(days=1),
        district_key=ndb.Key(District, "2026ne"),
    )
    event_without_webcast_ne.put()

    week_events_mock.return_value = [
        event_with_webcast,
        event_without_webcast,
        event_without_webcast_ne,
    ]
    live_events_mock.return_value = ({}, [])

    resp = tasks_client.get("/tasks/do/update_live_events")
    assert resp.status_code == 200

    firebase_mock.assert_called_once()

    # Check that tasks were enqueued for the districts with events without webcasts
    tasks = taskqueue_stub.get_filtered_tasks(queue_names="default")
    assert len(tasks) == 2
    task_urls = {t.url for t in tasks}
    assert "/tasks/do/find_event_webcasts/2026fim" in task_urls
    assert "/tasks/do/find_event_webcasts/2026ne" in task_urls


@mock.patch.object(FirebasePusher, "update_live_events")
@mock.patch.object(LiveEventHelper, "get_live_events_with_current_webcasts")
@mock.patch.object(EventHelper, "week_events")
def test_update_live_events_no_district_tasks_when_not_needed(
    week_events_mock: mock.Mock,
    live_events_mock: mock.Mock,
    firebase_mock: mock.Mock,
    tasks_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:
    # Setup district webcast channel configuration
    set_district_webcast_channels(
        "fim",
        [
            WebcastChannel(
                type=WebcastType.YOUTUBE,
                channel="FIRST in Michigan",
                channel_id="UCjX4WSaAFPgM2PYr-6P",
            )
        ],
    )

    # Event with webcast - should not trigger district search
    event_with_webcast = Event(
        id="2026fim1",
        year=2026,
        event_short="fim1",
        event_type_enum=EventType.DISTRICT,
        start_date=datetime.datetime.now(),
        end_date=datetime.datetime.now() + datetime.timedelta(days=1),
        district_key=ndb.Key(District, "2026fim"),
        webcast_json=json.dumps(
            [Webcast(type=WebcastType.YOUTUBE, channel="existing123")]
        ),
    )
    event_with_webcast.put()

    week_events_mock.return_value = [event_with_webcast]
    live_events_mock.return_value = ({}, [])

    resp = tasks_client.get("/tasks/do/update_live_events")
    assert resp.status_code == 200

    # No tasks should be enqueued
    tasks = taskqueue_stub.get_filtered_tasks(queue_names="default")
    assert len(tasks) == 0


@mock.patch.object(FirebasePusher, "update_live_events")
@mock.patch.object(LiveEventHelper, "get_live_events_with_current_webcasts")
@mock.patch.object(EventHelper, "week_events")
def test_update_live_events_no_district_tasks_for_unsupported_districts(
    week_events_mock: mock.Mock,
    live_events_mock: mock.Mock,
    firebase_mock: mock.Mock,
    tasks_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:
    # Setup district webcast channel configuration with only 'fim'
    set_district_webcast_channels(
        "fim",
        [
            WebcastChannel(
                type=WebcastType.YOUTUBE,
                channel="FIRST in Michigan",
                channel_id="UCjX4WSaAFPgM2PYr-6P",
            )
        ],
    )

    # Event without webcast but in unsupported district
    event_unsupported_district = Event(
        id="2026ne1",
        year=2026,
        event_short="ne1",
        event_type_enum=EventType.DISTRICT,
        start_date=datetime.datetime.now(),
        end_date=datetime.datetime.now() + datetime.timedelta(days=1),
        district_key=ndb.Key(District, "2026ne"),  # 'ne' is not in supported list
    )
    event_unsupported_district.put()

    week_events_mock.return_value = [event_unsupported_district]
    live_events_mock.return_value = ({}, [])

    resp = tasks_client.get("/tasks/do/update_live_events")
    assert resp.status_code == 200

    # No tasks should be enqueued for unsupported district
    tasks = taskqueue_stub.get_filtered_tasks(queue_names="default")
    assert len(tasks) == 0


def test_find_event_webcasts_district_not_supported(tasks_client: Client) -> None:
    resp = tasks_client.get("/tasks/do/find_event_webcasts/2026fim")
    assert resp.status_code == 400


def test_find_event_webcasts_non_youtube_type(tasks_client: Client) -> None:
    set_district_webcast_channels(
        "fim",
        [
            WebcastChannel(
                type=WebcastType.TWITCH,
                channel="firstinmichigan",
                channel_id="",
            )
        ],
    )

    resp = tasks_client.get("/tasks/do/find_event_webcasts/2026fim")
    assert resp.status_code == 400


@freeze_time("2026-03-15")
@mock.patch.object(EventWebcastAdder, "add_webcast")
@mock.patch.object(YouTubeVideoHelper, "get_scheduled_start_time")
@mock.patch.object(YouTubeVideoHelper, "get_upcoming_streams")
def test_find_event_webcasts_successful_match(
    get_streams_mock: mock.Mock,
    get_start_time_mock: mock.Mock,
    add_webcast_mock: mock.Mock,
    tasks_client: Client,
    ndb_stub,
) -> None:
    # Setup district and events
    District(id="2026fim", year=2026, abbreviation="fim").put()
    event = Event(
        id="2026fim1",
        year=2026,
        event_short="fim1",
        short_name="Troy",
        event_type_enum=EventType.DISTRICT,
        start_date=datetime.datetime.now(),
        end_date=datetime.datetime.now() + datetime.timedelta(days=1),
        district_key=ndb.Key(District, "2026fim"),
    )
    event.put()

    set_district_webcast_channels(
        "fim",
        [
            WebcastChannel(
                type=WebcastType.YOUTUBE,
                channel="FIRST in Michigan",
                channel_id="UCjX4WSaAFPgM2PYr-6P",
            )
        ],
    )

    # Mock upcoming streams
    get_streams_mock.return_value = InstantFuture(
        [
            YouTubeUpcomingStream(
                stream_id="abc123",
                title="Troy District Event - Qualifications",
                scheduled_start_time="",
            )
        ]
    )
    # Mock start time retrieval
    get_start_time_mock.return_value = InstantFuture("2026-03-15")

    resp = tasks_client.get("/tasks/do/find_event_webcasts/2026fim")
    assert resp.status_code == 200
    assert b"Discovered webcasts:" in resp.data
    assert b"2026fim1: abc123 (2026-03-15)" in resp.data

    # Verify webcast was added
    add_webcast_mock.assert_called_once()
    call_args = add_webcast_mock.call_args
    assert call_args[0][0].key_name == "2026fim1"
    added_webcast = call_args[0][1]
    assert added_webcast["type"] == WebcastType.YOUTUBE
    assert added_webcast["channel"] == "abc123"
    assert added_webcast["date"] == "2026-03-15"


@freeze_time("2026-03-15")
@mock.patch.object(EventWebcastAdder, "add_webcast")
@mock.patch.object(YouTubeVideoHelper, "get_scheduled_start_time")
@mock.patch.object(YouTubeVideoHelper, "get_upcoming_streams")
def test_find_event_webcasts_multiple_streams_for_event(
    get_streams_mock: mock.Mock,
    get_start_time_mock: mock.Mock,
    add_webcast_mock: mock.Mock,
    tasks_client: Client,
    ndb_stub,
) -> None:
    # Setup district and events
    District(id="2026fim", year=2026, abbreviation="fim").put()
    event = Event(
        id="2026fim1",
        year=2026,
        event_short="fim1",
        short_name="Troy",
        event_type_enum=EventType.DISTRICT,
        start_date=datetime.datetime.now(),
        end_date=datetime.datetime.now() + datetime.timedelta(days=1),
        district_key=ndb.Key(District, "2026fim"),
    )
    event.put()

    set_district_webcast_channels(
        "fim",
        [
            WebcastChannel(
                type=WebcastType.YOUTUBE,
                channel="FIRST in Michigan",
                channel_id="UCjX4WSaAFPgM2PYr-6P",
            )
        ],
    )

    # Mock multiple upcoming streams for the same event
    get_streams_mock.return_value = InstantFuture(
        [
            YouTubeUpcomingStream(
                stream_id="abc123",
                title="Troy District Event - Qualifications",
                scheduled_start_time="",
            ),
            YouTubeUpcomingStream(
                stream_id="def456",
                title="Troy District Event - Playoffs",
                scheduled_start_time="",
            ),
        ]
    )
    # Mock start time retrieval for both streams
    get_start_time_mock.side_effect = [
        InstantFuture("2026-03-15"),
        InstantFuture("2026-03-16"),
    ]

    resp = tasks_client.get("/tasks/do/find_event_webcasts/2026fim")
    assert resp.status_code == 200

    # Verify both webcasts were added
    assert add_webcast_mock.call_count == 2


@freeze_time("2026-03-15")
@mock.patch.object(EventWebcastAdder, "add_webcast")
@mock.patch.object(YouTubeVideoHelper, "get_scheduled_start_time")
@mock.patch.object(YouTubeVideoHelper, "get_upcoming_streams")
def test_find_event_webcasts_multiple_event_match_skipped(
    get_streams_mock: mock.Mock,
    get_start_time_mock: mock.Mock,
    add_webcast_mock: mock.Mock,
    tasks_client: Client,
    ndb_stub,
    caplog,
) -> None:
    # Setup district and events with same string in short_name
    District(id="2026fim", year=2026, abbreviation="fim").put()
    event1 = Event(
        id="2026fim1",
        year=2026,
        event_short="fim1",
        short_name="Troy",
        event_type_enum=EventType.DISTRICT,
        start_date=datetime.datetime.now(),
        end_date=datetime.datetime.now() + datetime.timedelta(days=1),
        district_key=ndb.Key(District, "2026fim"),
    )
    event1.put()
    event2 = Event(
        id="2026fim2",
        year=2026,
        event_short="fim2",
        short_name="Troy Albany",  # Also contains "Troy"
        event_type_enum=EventType.DISTRICT,
        start_date=datetime.datetime.now(),
        end_date=datetime.datetime.now() + datetime.timedelta(days=1),
        district_key=ndb.Key(District, "2026fim"),
    )
    event2.put()

    set_district_webcast_channels(
        "fim",
        [
            WebcastChannel(
                type=WebcastType.YOUTUBE,
                channel="FIRST in Michigan",
                channel_id="UCjX4WSaAFPgM2PYr-6P",
            )
        ],
    )

    # Mock stream that matches both events (both have "Troy" in their short_name)
    # and both event names appear in the stream title
    get_streams_mock.return_value = InstantFuture(
        [
            YouTubeUpcomingStream(
                stream_id="abc123",
                title="2026 FIM Troy and Troy Albany District Events",  # Contains both "Troy" and "Troy Albany"
                scheduled_start_time="",
            )
        ]
    )

    resp = tasks_client.get("/tasks/do/find_event_webcasts/2026fim")
    assert resp.status_code == 200

    # Verify no webcast was added due to ambiguity
    add_webcast_mock.assert_not_called()

    # Verify info message was logged
    assert "Multiple matched events for stream abc123" in caplog.text


@freeze_time("2026-03-15")
@mock.patch.object(EventWebcastAdder, "add_webcast")
@mock.patch.object(YouTubeVideoHelper, "get_upcoming_streams")
def test_find_event_webcasts_no_matching_events(
    get_streams_mock: mock.Mock,
    add_webcast_mock: mock.Mock,
    tasks_client: Client,
    ndb_stub,
) -> None:
    # Setup district and event
    District(id="2026fim", year=2026, abbreviation="fim").put()
    event = Event(
        id="2026fim1",
        year=2026,
        event_short="fim1",
        short_name="Troy",
        event_type_enum=EventType.DISTRICT,
        start_date=datetime.datetime.now(),
        end_date=datetime.datetime.now() + datetime.timedelta(days=1),
        district_key=ndb.Key(District, "2026fim"),
    )
    event.put()

    set_district_webcast_channels(
        "fim",
        [
            WebcastChannel(
                type=WebcastType.YOUTUBE,
                channel="FIRST in Michigan",
                channel_id="UCjX4WSaAFPgM2PYr-6P",
            )
        ],
    )

    # Mock stream that doesn't match any event
    get_streams_mock.return_value = InstantFuture(
        [
            YouTubeUpcomingStream(
                stream_id="abc123",
                title="Unrelated Stream Title",
                scheduled_start_time="",
            )
        ]
    )

    resp = tasks_client.get("/tasks/do/find_event_webcasts/2026fim")
    assert resp.status_code == 200
    assert resp.data == b"Discovered webcasts: none"

    # Verify no webcast was added
    add_webcast_mock.assert_not_called()


@freeze_time("2026-03-15")
@mock.patch.object(EventWebcastAdder, "add_webcast")
@mock.patch.object(YouTubeVideoHelper, "get_scheduled_start_time")
@mock.patch.object(YouTubeVideoHelper, "get_upcoming_streams")
def test_find_event_webcasts_no_output_in_taskqueue(
    get_streams_mock: mock.Mock,
    get_start_time_mock: mock.Mock,
    add_webcast_mock: mock.Mock,
    tasks_client: Client,
    ndb_stub,
) -> None:
    District(id="2026fim", year=2026, abbreviation="fim").put()
    Event(
        id="2026fim1",
        year=2026,
        event_short="fim1",
        short_name="Troy",
        event_type_enum=EventType.DISTRICT,
        start_date=datetime.datetime.now(),
        end_date=datetime.datetime.now() + datetime.timedelta(days=1),
        district_key=ndb.Key(District, "2026fim"),
    ).put()

    set_district_webcast_channels(
        "fim",
        [
            WebcastChannel(
                type=WebcastType.YOUTUBE,
                channel="FIRST in Michigan",
                channel_id="UCjX4WSaAFPgM2PYr-6P",
            )
        ],
    )

    get_streams_mock.return_value = InstantFuture(
        [
            YouTubeUpcomingStream(
                stream_id="abc123",
                title="Troy District Event - Qualifications",
                scheduled_start_time="",
            )
        ]
    )
    get_start_time_mock.return_value = InstantFuture("2026-03-15")

    resp = tasks_client.get(
        "/tasks/do/find_event_webcasts/2026fim",
        headers={"X-Appengine-Taskname": "test"},
    )
    assert resp.status_code == 200
    assert resp.data == b""
    add_webcast_mock.assert_called_once()


@freeze_time("2026-03-15")
@mock.patch.object(EventWebcastAdder, "add_webcast")
@mock.patch.object(YouTubeVideoHelper, "get_scheduled_start_time")
@mock.patch.object(YouTubeVideoHelper, "get_upcoming_streams")
def test_find_event_webcasts_no_start_time_skipped(
    get_streams_mock: mock.Mock,
    get_start_time_mock: mock.Mock,
    add_webcast_mock: mock.Mock,
    tasks_client: Client,
    ndb_stub,
    caplog,
) -> None:
    # Setup district and event
    District(id="2026fim", year=2026, abbreviation="fim").put()
    event = Event(
        id="2026fim1",
        year=2026,
        event_short="fim1",
        short_name="Troy",
        event_type_enum=EventType.DISTRICT,
        start_date=datetime.datetime.now(),
        end_date=datetime.datetime.now() + datetime.timedelta(days=1),
        district_key=ndb.Key(District, "2026fim"),
    )
    event.put()

    set_district_webcast_channels(
        "fim",
        [
            WebcastChannel(
                type=WebcastType.YOUTUBE,
                channel="FIRST in Michigan",
                channel_id="UCjX4WSaAFPgM2PYr-6P",
            )
        ],
    )

    # Mock stream
    get_streams_mock.return_value = InstantFuture(
        [
            YouTubeUpcomingStream(
                stream_id="abc123",
                title="Troy District Event",
                scheduled_start_time="",
            )
        ]
    )
    # Mock start time retrieval returning None
    get_start_time_mock.return_value = InstantFuture(None)

    resp = tasks_client.get("/tasks/do/find_event_webcasts/2026fim")
    assert resp.status_code == 200

    # Verify no webcast was added due to missing start time
    add_webcast_mock.assert_not_called()

    # Verify info message was logged
    assert "Could not find start time for stream" in caplog.text


@freeze_time("2026-03-15")
@mock.patch.object(YouTubeVideoHelper, "get_upcoming_streams")
def test_find_event_webcasts_no_live_events(
    get_streams_mock: mock.Mock,
    tasks_client: Client,
    ndb_stub,
) -> None:
    # Setup district but no events within a day
    District(id="2026fim", year=2026, abbreviation="fim").put()
    event = Event(
        id="2026fim1",
        year=2026,
        event_short="fim1",
        short_name="Troy",
        event_type_enum=EventType.DISTRICT,
        start_date=datetime.datetime.now() + datetime.timedelta(days=10),
        end_date=datetime.datetime.now() + datetime.timedelta(days=11),
        district_key=ndb.Key(District, "2026fim"),
    )
    event.put()

    set_district_webcast_channels(
        "fim",
        [
            WebcastChannel(
                type=WebcastType.YOUTUBE,
                channel="FIRST in Michigan",
                channel_id="UCjX4WSaAFPgM2PYr-6P",
            )
        ],
    )

    # Mock streams
    get_streams_mock.return_value = InstantFuture(
        [
            YouTubeUpcomingStream(
                stream_id="abc123",
                title="Troy District Event",
                scheduled_start_time="",
            )
        ]
    )

    resp = tasks_client.get("/tasks/do/find_event_webcasts/2026fim")
    assert resp.status_code == 200

    # Stream lookup should still be called, but no events to match
    get_streams_mock.assert_called_once()
