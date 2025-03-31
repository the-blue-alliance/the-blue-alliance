import datetime
from unittest import mock

from freezegun import freeze_time
from google.appengine.ext import ndb, testbed
from werkzeug.test import Client

from backend.common.consts.event_type import EventType
from backend.common.futures import InstantFuture
from backend.common.helpers.season_helper import SeasonHelper
from backend.common.models.event import Event
from backend.common.models.event_team import EventTeam
from backend.common.models.event_team_pit_location import EventTeamPitLocation
from backend.common.models.keys import EventKey, TeamKey
from backend.common.models.team import Team
from backend.tasks_io.datafeeds.datafeed_nexus import NexusPitLocations


def create_event(official: bool) -> Event:
    e = Event(
        id="2019casj",
        year=2019,
        event_short="casj",
        start_date=datetime.datetime(2019, 4, 1),
        end_date=datetime.datetime(2019, 4, 3),
        event_type_enum=EventType.REGIONAL,
        official=official,
    )
    e.put()
    return e


def create_eventteam(event_key: EventKey, team_key: TeamKey) -> EventTeam:
    et = EventTeam(
        id=f"{event_key}_{team_key}",
        year=int(event_key[:4]),
        event=ndb.Key(Event, event_key),
        team=ndb.Key(Team, team_key),
    )
    et.put()
    return et


@freeze_time("2019-04-01")
def test_enqueue_current(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    create_event(official=True)

    resp = tasks_client.get("/tasks/enqueue/nexus_pit_locations/now")
    assert resp.status_code == 200
    assert len(resp.data) > 0

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="datafeed")
    assert len(tasks) == 1
    assert tasks[0].url == "/tasks/get/nexus_pit_locations/2019casj"


@freeze_time("2019-04-01")
def test_enqueue_current_no_write_in_taskqueue(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    create_event(official=True)

    resp = tasks_client.get(
        "/tasks/enqueue/nexus_pit_locations/now",
        headers={"X-Appengine-Taskname": "test"},
    )
    assert resp.status_code == 200
    assert len(resp.data) == 0

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="datafeed")
    assert len(tasks) == 1
    assert tasks[0].url == "/tasks/get/nexus_pit_locations/2019casj"


@freeze_time("2019-04-01")
def test_enqueue_current_skips_unofficial(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    create_event(official=False)

    resp = tasks_client.get("/tasks/enqueue/nexus_pit_locations/now")
    assert resp.status_code == 200
    assert len(resp.data) > 0

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="datafeed")
    assert len(tasks) == 0


@freeze_time("2019-01-01")
@mock.patch.object(SeasonHelper, "get_current_season")
def test_enqueue_season(
    season_mock,
    tasks_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:
    season_mock.return_value = 2019
    create_event(official=True)

    resp = tasks_client.get("/tasks/enqueue/nexus_pit_locations/current_year")
    assert resp.status_code == 200
    assert len(resp.data) > 0

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="datafeed")
    assert len(tasks) == 1
    assert tasks[0].url == "/tasks/get/nexus_pit_locations/2019casj"


@freeze_time("2019-01-01")
@mock.patch.object(SeasonHelper, "get_current_season")
def test_enqueue_season_skips_unofficial(
    season_mock,
    tasks_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:
    season_mock.return_value = 2019
    create_event(official=False)

    resp = tasks_client.get("/tasks/enqueue/nexus_pit_locations/current_year")
    assert resp.status_code == 200
    assert len(resp.data) > 0

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="datafeed")
    assert len(tasks) == 0


def test_enqueue_year(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    create_event(official=True)

    resp = tasks_client.get("/tasks/enqueue/nexus_pit_locations/2019")
    assert resp.status_code == 200
    assert len(resp.data) > 0

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="datafeed")
    assert len(tasks) == 1
    assert tasks[0].url == "/tasks/get/nexus_pit_locations/2019casj"


def test_enqueue_year_skips_unofficial(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    create_event(official=False)

    resp = tasks_client.get("/tasks/enqueue/nexus_pit_locations/2019")
    assert resp.status_code == 200
    assert len(resp.data) > 0

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="datafeed")
    assert len(tasks) == 0


def test_fetch_bad_key(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    resp = tasks_client.get("/tasks/get/nexus_pit_locations/zzzz")
    assert resp.status_code == 400


def test_fetch_missing_event(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    resp = tasks_client.get("/tasks/get/nexus_pit_locations/2019casj")
    assert resp.status_code == 404


@mock.patch.object(NexusPitLocations, "fetch_async")
def test_fetch_updates_eventteam(
    nexus_api_mock,
    tasks_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:
    create_event(official=True)
    create_eventteam("2019casj", "frc254")

    pit_location = EventTeamPitLocation(location="A1")
    nexus_api_mock.return_value = InstantFuture({"frc254": pit_location})

    resp = tasks_client.get("/tasks/get/nexus_pit_locations/2019casj")
    assert resp.status_code == 200
    assert len(resp.data) > 0

    et = EventTeam.get_by_id("2019casj_frc254")
    assert et is not None
    assert et.pit_location == pit_location


@mock.patch.object(NexusPitLocations, "fetch_async")
def test_fetch_updates_eventteam_skip_missing(
    nexus_api_mock,
    tasks_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:
    create_event(official=True)
    create_eventteam("2019casj", "frc254")

    nexus_api_mock.return_value = InstantFuture({})

    resp = tasks_client.get("/tasks/get/nexus_pit_locations/2019casj")
    assert resp.status_code == 200
    assert len(resp.data) > 0

    et = EventTeam.get_by_id("2019casj_frc254")
    assert et is not None
    assert et.pit_location is None


@mock.patch.object(NexusPitLocations, "fetch_async")
def test_fetch_updates_eventteam_no_write_in_taskqueue(
    nexus_api_mock,
    tasks_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:
    create_event(official=True)
    create_eventteam("2019casj", "frc254")

    pit_location = EventTeamPitLocation(location="A1")
    nexus_api_mock.return_value = InstantFuture({"frc254": pit_location})

    resp = tasks_client.get(
        "/tasks/get/nexus_pit_locations/2019casj",
        headers={"X-Appengine-Taskname": "test"},
    )
    assert resp.status_code == 200
    assert len(resp.data) == 0

    et = EventTeam.get_by_id("2019casj_frc254")
    assert et is not None
    assert et.pit_location == pit_location
