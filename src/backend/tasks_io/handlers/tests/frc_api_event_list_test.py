import datetime
from unittest import mock

from google.appengine.ext import testbed
from werkzeug.test import Client

from backend.common.consts.event_type import EventType
from backend.common.futures import InstantFuture
from backend.common.models.district import District
from backend.common.models.event import Event
from backend.common.sitevars.apistatus import ApiStatus
from backend.tasks_io.datafeeds.datafeed_fms_api import DatafeedFMSAPI


def test_enqueue_bad_when(tasks_client: Client) -> None:
    resp = tasks_client.get("/backend-tasks/enqueue/event_list/asdf")
    assert resp.status_code == 404


def test_enqueue_current(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    ApiStatus.put(
        {
            "current_season": 2020,
            "max_season": 2022,
            "android": None,
            "ios": None,
            "web": None,
            "max_team_page": 0,
        }
    )
    resp = tasks_client.get("/backend-tasks/enqueue/event_list/current")
    assert resp.status_code == 200
    assert len(resp.data) > 0

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="datafeed")
    assert len(tasks) == 3

    expected_years = [2020, 2021, 2022]
    assert [f"/backend-tasks/get/event_list/{year}" for year in expected_years] == [
        t.url for t in tasks
    ]


def test_enqueue_current_no_output_in_taskqueue(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    ApiStatus.put(
        {
            "current_season": 2020,
            "max_season": 2022,
            "android": None,
            "ios": None,
            "web": None,
            "max_team_page": 0,
        }
    )
    resp = tasks_client.get(
        "/backend-tasks/enqueue/event_list/current",
        headers={"X-Appengine-Taskname": "test"},
    )
    assert resp.status_code == 200
    assert len(resp.data) == 0

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="datafeed")
    assert len(tasks) == 3


def test_enqueue_explicit_year(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    resp = tasks_client.get("/backend-tasks/enqueue/event_list/2020")
    assert resp.status_code == 200

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="datafeed")
    assert len(tasks) == 1
    assert tasks[0].url == "/backend-tasks/get/event_list/2020"


def test_get_bad_year(tasks_client: Client) -> None:
    resp = tasks_client.get("/backend-tasks/get/event_list/asdf")
    assert resp.status_code == 404


@mock.patch.object(DatafeedFMSAPI, "get_district_list")
@mock.patch.object(DatafeedFMSAPI, "get_event_list")
def test_get_no_events(
    event_list_mock, district_list_mock, tasks_client: Client
) -> None:
    event_list_mock.return_value = InstantFuture(([], []))
    district_list_mock.return_value = InstantFuture([])

    resp = tasks_client.get("/backend-tasks/get/event_list/2020")
    assert resp.status_code == 200
    assert len(resp.data) > 0


@mock.patch.object(DatafeedFMSAPI, "get_district_list")
@mock.patch.object(DatafeedFMSAPI, "get_event_list")
def test_get_no_events_no_output_in_taskqueue(
    event_list_mock, district_list_mock, tasks_client: Client
) -> None:
    event_list_mock.return_value = InstantFuture(([], []))
    district_list_mock.return_value = InstantFuture([])

    resp = tasks_client.get(
        "/backend-tasks/get/event_list/2020",
        headers={"X-Appengine-Taskname": "test"},
    )
    assert resp.status_code == 200
    assert len(resp.data) == 0


@mock.patch.object(DatafeedFMSAPI, "get_district_list")
@mock.patch.object(DatafeedFMSAPI, "get_event_list")
def test_get(
    event_list_mock,
    district_list_mock,
    tasks_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:
    events = [
        Event(
            id="2019casj",
            year=2019,
            event_short="casj",
            start_date=datetime.datetime(2019, 4, 1),
            end_date=datetime.datetime(2019, 4, 3),
            event_type_enum=EventType.REGIONAL,
        )
    ]
    districts = [
        District(
            id="2019fim",
            year=2019,
            abbreviation="fim",
        )
    ]
    event_list_mock.return_value = InstantFuture((events, districts))
    district_list_mock.return_value = InstantFuture(districts)

    resp = tasks_client.get("/backend-tasks/get/event_list/2019")
    assert resp.status_code == 200
    assert len(resp.data) > 0

    # Make sure we write objects
    assert Event.get_by_id("2019casj") is not None
    assert District.get_by_id("2019fim") is not None

    # Make sure we enqueue event details fetches
    tasks = taskqueue_stub.get_filtered_tasks(queue_names="datafeed")
    assert len(tasks) == 1
    assert tasks[0].url == "/backend-tasks/get/event_details/2019casj"


@mock.patch.object(DatafeedFMSAPI, "get_district_list")
@mock.patch.object(DatafeedFMSAPI, "get_event_list")
def test_get_match_offseasons(
    event_list_mock,
    district_list_mock,
    tasks_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:
    Event(
        id="2019casj_tba",
        year=2019,
        event_short="casj",
        start_date=datetime.datetime(2019, 4, 1),
        end_date=datetime.datetime(2019, 4, 3),
        event_type_enum=EventType.OFFSEASON,
    ).put()

    events = [
        Event(
            id="2019casj",
            year=2019,
            event_short="casj",
            start_date=datetime.datetime(2019, 4, 1),
            end_date=datetime.datetime(2019, 4, 3),
            event_type_enum=EventType.OFFSEASON,
        )
    ]
    districts = [
        District(
            id="2019fim",
            year=2019,
            abbreviation="fim",
        )
    ]
    event_list_mock.return_value = InstantFuture((events, districts))
    district_list_mock.return_value = InstantFuture(districts)

    resp = tasks_client.get("/backend-tasks/get/event_list/2019")
    assert resp.status_code == 200
    assert len(resp.data) > 0

    # Make sure we write objects
    e = Event.get_by_id("2019casj_tba")
    assert e is not None
    assert e.first_code == "casj"

    assert Event.get_by_id("2019casj") is None
    assert District.get_by_id("2019fim") is not None

    # Make sure we enqueue event details fetches
    tasks = taskqueue_stub.get_filtered_tasks(queue_names="datafeed")
    assert len(tasks) == 1
    assert tasks[0].url == "/backend-tasks/get/event_details/2019casj"
