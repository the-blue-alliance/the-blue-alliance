import datetime
from unittest import mock

from freezegun import freeze_time
from google.appengine.ext import ndb, testbed
from werkzeug.test import Client

from backend.common.consts.comp_level import CompLevel
from backend.common.consts.event_type import EventType
from backend.common.futures import InstantFuture
from backend.common.helpers.firebase_pusher import FirebasePusher
from backend.common.memcache_models.event_nexus_queue_status_memcache import (
    EventNexusQueueStatusMemcache,
)
from backend.common.models.event import Event
from backend.common.models.event_queue_status import (
    EventQueueStatus,
    NexusCurrentlyQueueing,
    NexusMatch,
    NexusMatchStatus,
    NexusMatchTiming,
)
from backend.common.models.match import Match
from backend.tasks_io.datafeeds.datafeed_nexus import DatafeedNexus


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


def create_match() -> Match:
    m = Match(
        id="2019casj_qm1",
        event=ndb.Key(Event, "2019casj"),
        comp_level=CompLevel.QM,
        match_number=1,
        set_number=1,
        year=2019,
        alliances_json="",
    )
    m.put()
    return m


@freeze_time("2019-04-01")
def test_enqueue_current(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    create_event(official=True)

    resp = tasks_client.get("/tasks/enqueue/nexus_queue_status/now")
    assert resp.status_code == 200
    assert len(resp.data) > 0

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="datafeed")
    assert len(tasks) == 1
    assert tasks[0].url == "/tasks/get/nexus_queue_status/2019casj"


@freeze_time("2019-04-01")
def test_enqueue_current_no_write_in_taskqueue(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    create_event(official=True)

    resp = tasks_client.get(
        "/tasks/enqueue/nexus_queue_status/now",
        headers={"X-Appengine-Taskname": "test"},
    )
    assert resp.status_code == 200
    assert len(resp.data) == 0

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="datafeed")
    assert len(tasks) == 1
    assert tasks[0].url == "/tasks/get/nexus_queue_status/2019casj"


@freeze_time("2019-04-01")
def test_enqueue_current_skips_unofficial(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    create_event(official=False)

    resp = tasks_client.get("/tasks/enqueue/nexus_queue_status/now")
    assert resp.status_code == 200
    assert len(resp.data) > 0

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="datafeed")
    assert len(tasks) == 0


def test_fetch_bad_key(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    resp = tasks_client.get("/tasks/get/nexus_queue_status/asdf")
    assert resp.status_code == 400


def test_fetch_missing_event(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    resp = tasks_client.get("/tasks/get/nexus_queue_status/2019casj")
    assert resp.status_code == 404


@mock.patch.object(FirebasePusher, "update_match_queue_status")
@mock.patch.object(DatafeedNexus, "get_event_queue_status")
def test_fetch_updates_downstream(
    nexus_mock: mock.Mock,
    firebase_mock: mock.Mock,
    tasks_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
    memcache_stub: testbed.memcache_stub.MemcacheServiceStub,
) -> None:
    create_event(official=True)
    m = create_match()

    status = EventQueueStatus(
        data_as_of_ms=0,
        now_queueing=NexusCurrentlyQueueing(
            match_key="2019casj_qm1",
            match_name="Quals 1",
        ),
        matches={
            "2019casj_qm1": NexusMatch(
                label="Quals 1",
                status=NexusMatchStatus.NOW_QUEUING,
                played=False,
                times=NexusMatchTiming(
                    estimated_queue_time_ms=0,
                    estimated_start_time_ms=0,
                ),
            ),
        },
    )
    nexus_mock.return_value = InstantFuture(status)

    resp = tasks_client.get("/tasks/get/nexus_queue_status/2019casj")
    assert resp.status_code == 200
    assert len(resp.data) > 0

    # Ensure we write to memcache
    cache_data = EventNexusQueueStatusMemcache("2019casj").get()
    assert cache_data == status

    # Ensure we write to firebase
    firebase_mock.assert_called_once_with(m, status)


@mock.patch.object(FirebasePusher, "update_match_queue_status")
@mock.patch.object(DatafeedNexus, "get_event_queue_status")
def test_fetch_no_write_in_taskqueue(
    nexus_mock: mock.Mock,
    firebase_mock: mock.Mock,
    tasks_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
    memcache_stub: testbed.memcache_stub.MemcacheServiceStub,
) -> None:
    create_event(official=True)
    create_match()

    status = EventQueueStatus(
        data_as_of_ms=0,
        now_queueing=NexusCurrentlyQueueing(
            match_key="2019casj_qm1",
            match_name="Quals 1",
        ),
        matches={
            "2019casj_qm1": NexusMatch(
                label="Quals 1",
                status=NexusMatchStatus.NOW_QUEUING,
                played=False,
                times=NexusMatchTiming(
                    estimated_queue_time_ms=0,
                    estimated_start_time_ms=0,
                ),
            ),
        },
    )
    nexus_mock.return_value = InstantFuture(status)

    resp = tasks_client.get(
        "/tasks/get/nexus_queue_status/2019casj",
        headers={"X-Appengine-Taskname": "test"},
    )
    assert resp.status_code == 200
    assert len(resp.data) == 0
