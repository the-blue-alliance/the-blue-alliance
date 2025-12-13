from unittest import mock

from google.appengine.ext import ndb, testbed
from werkzeug.test import Client

from backend.common.consts.event_type import EventType
from backend.common.helpers.regional_champs_pool_helper import RegionalChampsPoolHelper
from backend.common.models.district import District
from backend.common.models.event import Event
from backend.common.models.event_details import EventDetails
from backend.common.models.event_district_points import (
    EventDistrictPoints,
    TeamAtEventDistrictPoints,
    TeamAtEventDistrictPointTiebreakers,
)


def test_regional_pool_calc_no_event(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    resp = tasks_client.get("/tasks/math/do/regional_champs_pool_points_calc/2025test")
    assert resp.status_code == 404

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="default")
    assert len(tasks) == 0


def test_regional_pool_calc_bad_year(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    Event(
        id="2020test",
        year=2020,
        event_short="event",
        event_type_enum=EventType.DISTRICT,
        district_key=ndb.Key(District, "2020ne"),
    ).put()
    resp = tasks_client.get("/tasks/math/do/regional_champs_pool_points_calc/2020test")
    assert resp.status_code == 400

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="default")
    assert len(tasks) == 0


def test_regional_pool_calc_non_regional(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    Event(
        id="2025test",
        year=2025,
        event_short="event",
        event_type_enum=EventType.DISTRICT,
        district_key=ndb.Key(District, "2025ne"),
    ).put()
    resp = tasks_client.get("/tasks/math/do/regional_champs_pool_points_calc/2025test")
    assert resp.status_code == 400

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="default")
    assert len(tasks) == 0


@mock.patch.object(RegionalChampsPoolHelper, "calculate_event_points")
def test_regional_pool_calc(
    calc_mock: mock.Mock,
    tasks_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:
    Event(
        id="2025test",
        year=2025,
        event_short="test",
        event_type_enum=EventType.REGIONAL,
    ).put()
    points = EventDistrictPoints(
        points={
            "frc254": TeamAtEventDistrictPoints(
                event_key="2025test",
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

    resp = tasks_client.get("/tasks/math/do/regional_champs_pool_points_calc/2025test")
    assert resp.status_code == 200
    assert len(resp.data) > 0

    event_detail = EventDetails.get_by_id("2025test")
    assert event_detail is not None
    assert event_detail.district_points is None
    assert event_detail.regional_champs_pool_points == points

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="default")
    task_urls = {t.url for t in tasks}
    assert {"/tasks/math/do/regional_champs_pool_rankings_calc/2025"} == task_urls

    for task in tasks:
        task_resp = tasks_client.get(task.url)
        assert task_resp.status_code == 200


@mock.patch.object(RegionalChampsPoolHelper, "calculate_event_points")
def test_regional_pool_calc_no_output_in_taskqueue(
    calc_mock: mock.Mock,
    tasks_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:
    Event(
        id="2025test",
        year=2025,
        event_short="test",
        event_type_enum=EventType.REGIONAL,
    ).put()
    points = EventDistrictPoints(
        points={
            "frc254": TeamAtEventDistrictPoints(
                event_key="2025test",
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
        "/tasks/math/do/regional_champs_pool_points_calc/2025test",
        headers={
            "X-Appengine-Taskname": "test",
        },
    )
    assert resp.status_code == 200
    assert len(resp.data) == 0

    event_detail = EventDetails.get_by_id("2025test")
    assert event_detail is not None
    assert event_detail.district_points is None
    assert event_detail.regional_champs_pool_points == points

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="default")
    task_urls = {t.url for t in tasks}
    assert {"/tasks/math/do/regional_champs_pool_rankings_calc/2025"} == task_urls

    for task in tasks:
        task_resp = tasks_client.get(task.url)
        assert task_resp.status_code == 200
