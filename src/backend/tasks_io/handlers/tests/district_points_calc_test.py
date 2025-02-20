from unittest import mock

from freezegun import freeze_time
from google.appengine.ext import ndb, testbed
from werkzeug.test import Client

from backend.common.consts.event_type import EventType
from backend.common.helpers.district_helper import DistrictHelper
from backend.common.models.district import District
from backend.common.models.event import Event
from backend.common.models.event_details import EventDetails
from backend.common.models.event_district_points import (
    EventDistrictPoints,
    TeamAtEventDistrictPoints,
    TeamAtEventDistrictPointTiebreakers,
)


def test_enqueue_bad_year(tasks_client: Client) -> None:
    resp = tasks_client.get("/tasks/math/enqueue/district_points_calc/asdf")
    assert resp.status_code == 404


@freeze_time("2020-4-1")
def test_enqueue_no_events(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    resp = tasks_client.get("/tasks/math/enqueue/district_points_calc/2020")
    assert resp.status_code == 200
    assert resp.data == b"Enqueued for districts: []\nEnqueued for regionals: []"

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="default")
    assert len(tasks) == 0


@freeze_time("2020-4-1")
def test_enqueue_no_output_in_taskqueue(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    resp = tasks_client.get(
        "/tasks/math/enqueue/district_points_calc/2020",
        headers={
            "X-Appengine-Taskname": "test",
        },
    )
    assert resp.status_code == 200
    assert resp.data == b""

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="default")
    assert len(tasks) == 0


def test_enqueue_event(
    tasks_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
    ndb_stub,
) -> None:
    Event(
        id="2020event",
        year=2020,
        event_short="event",
        event_type_enum=EventType.REGIONAL,
    ).put()
    resp = tasks_client.get("/tasks/math/enqueue/district_points_calc/2020")
    assert resp.status_code == 200

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="default")
    assert len(tasks) == 1
    for task in tasks:
        task_resp = tasks_client.get(task.url)
        assert task_resp.status_code == 200


@freeze_time("2020-4-1")
def test_enqueue_event_defaults_to_current_year(
    tasks_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
    ndb_stub,
) -> None:
    Event(
        id="2020event",
        year=2020,
        event_short="event",
        event_type_enum=EventType.REGIONAL,
    ).put()
    resp = tasks_client.get("/tasks/math/enqueue/district_points_calc")
    assert resp.status_code == 200

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="default")
    assert len(tasks) == 1
    for task in tasks:
        task_resp = tasks_client.get(task.url)
        assert task_resp.status_code == 200


def test_enqueue_event_skips_offseason(
    tasks_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
    ndb_stub,
) -> None:
    Event(
        id="2020event",
        year=2020,
        event_short="event",
        event_type_enum=EventType.OFFSEASON,
    ).put()
    resp = tasks_client.get("/tasks/math/enqueue/district_points_calc/2020")
    assert resp.status_code == 200

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="default")
    assert len(tasks) == 0


def test_calc_no_event(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    resp = tasks_client.get("/tasks/math/do/district_points_calc/2020test")
    assert resp.status_code == 404

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="default")
    assert len(tasks) == 0


def test_calc_skips_offseason(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    Event(
        id="2020test",
        year=2020,
        event_short="event",
        event_type_enum=EventType.OFFSEASON,
    ).put()
    resp = tasks_client.get("/tasks/math/do/district_points_calc/2020test")
    assert resp.status_code == 400

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="default")
    assert len(tasks) == 0


def test_calc_skips_offseason_override(tasks_client: Client) -> None:
    Event(
        id="2020test",
        year=2020,
        event_short="event",
        event_type_enum=EventType.OFFSEASON,
    ).put()
    resp = tasks_client.get(
        "/tasks/math/do/district_points_calc/2020test?allow-offseason=true"
    )
    assert resp.status_code == 200


@mock.patch.object(DistrictHelper, "calculate_event_points")
def test_calc_regional(
    calc_mock: mock.Mock,
    tasks_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:
    Event(
        id="2020test",
        year=2020,
        event_short="event",
        event_type_enum=EventType.REGIONAL,
    ).put()
    points = EventDistrictPoints(
        points={
            "frc254": TeamAtEventDistrictPoints(
                event_key="2020test",
                district_cmp=False,
                qual_points=0,
                elim_points=0,
                alliance_points=0,
                award_points=0,
                total=0,
            )
        },
        tiebreakers={
            "frc254": TeamAtEventDistrictPointTiebreakers(
                qual_wins=0,
                highest_qual_scores=[],
            )
        },
    )
    calc_mock.return_value = points

    resp = tasks_client.get(
        "/tasks/math/do/district_points_calc/2020test?allow-offseason=true"
    )
    assert resp.status_code == 200
    assert len(resp.data) > 0

    event_detail = EventDetails.get_by_id("2020test")
    assert event_detail is not None
    assert event_detail.district_points == points

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="default")
    assert len(tasks) == 0


@mock.patch.object(DistrictHelper, "calculate_event_points")
def test_calc_regional_no_output_in_taskqueue(
    calc_mock: mock.Mock,
    tasks_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:
    Event(
        id="2020test",
        year=2020,
        event_short="event",
        event_type_enum=EventType.REGIONAL,
    ).put()
    points = EventDistrictPoints(
        points={},
        tiebreakers={},
    )
    calc_mock.return_value = points

    resp = tasks_client.get(
        "/tasks/math/do/district_points_calc/2020test?allow-offseason=true",
        headers={
            "X-Appengine-Taskname": "test",
        },
    )
    assert resp.status_code == 200
    assert len(resp.data) == 0

    event_detail = EventDetails.get_by_id("2020test")
    assert event_detail is not None
    assert event_detail.district_points == points

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="default")
    assert len(tasks) == 0


@mock.patch.object(DistrictHelper, "calculate_event_points")
def test_calc_district_enqueues_rankings(
    calc_mock: mock.Mock,
    tasks_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:
    Event(
        id="2020test",
        year=2020,
        event_short="event",
        event_type_enum=EventType.DISTRICT,
        district_key=ndb.Key(District, "2020ne"),
    ).put()
    District(
        id="2020ne",
        year=2020,
        abbreviation="ne",
    ).put()
    points = EventDistrictPoints(
        points={},
        tiebreakers={},
    )
    calc_mock.return_value = points

    resp = tasks_client.get(
        "/tasks/math/do/district_points_calc/2020test?allow-offseason=true",
        headers={
            "X-Appengine-Taskname": "test",
        },
    )
    assert resp.status_code == 200
    assert len(resp.data) == 0

    event_detail = EventDetails.get_by_id("2020test")
    assert event_detail is not None
    assert event_detail.district_points == points

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="default")
    assert len(tasks) == 1
    for task in tasks:
        task_resp = tasks_client.get(task.url)
        assert task_resp.status_code == 200
