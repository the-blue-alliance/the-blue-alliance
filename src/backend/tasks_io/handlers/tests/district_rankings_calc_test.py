from unittest import mock

import pytest
from freezegun import freeze_time
from google.appengine.ext import testbed
from werkzeug.test import Client

from backend.common.consts.event_type import EventType
from backend.common.futures import InstantFuture
from backend.common.helpers.district_helper import (
    DistrictHelper,
    DistrictRankingTeamTotal,
)
from backend.common.helpers.season_helper import SeasonHelper
from backend.common.models.district import District
from backend.common.models.district_ranking import DistrictRanking
from backend.common.models.event import Event
from backend.common.models.event_district_points import TeamAtEventDistrictPoints
from backend.tasks_io.datafeeds.datafeed_fms_api import DatafeedFMSAPI


def test_enqueue_bad_year(tasks_client: Client) -> None:
    resp = tasks_client.get("/tasks/math/enqueue/district_rankings_calc/asdf")
    assert resp.status_code == 404


@freeze_time("2020-4-1")
def test_enqueue_no_events(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    resp = tasks_client.get("/tasks/math/enqueue/district_rankings_calc/2020")
    assert resp.status_code == 200
    assert resp.data == b"Enqueued for: []"

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="default")
    assert len(tasks) == 0


@freeze_time("2020-4-1")
def test_enqueue_no_output_in_taskqueue(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    resp = tasks_client.get(
        "/tasks/math/enqueue/district_rankings_calc/2020",
        headers={
            "X-Appengine-Taskname": "test",
        },
    )
    assert resp.status_code == 200
    assert resp.data == b""

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="default")
    assert len(tasks) == 0


@mock.patch.object(DatafeedFMSAPI, "get_district_rankings")
def test_enqueue_event(
    district_rankings_mock,
    tasks_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
    ndb_stub,
) -> None:
    district_rankings_mock.return_value = InstantFuture({})
    District(
        id="2020test",
        year=2020,
        abbreviation="test",
    ).put()
    resp = tasks_client.get("/tasks/math/enqueue/district_rankings_calc/2020")
    assert resp.status_code == 200

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="default")
    assert len(tasks) == 2
    for task in tasks:
        task_resp = tasks_client.get(task.url)
        assert task_resp.status_code == 200

    taskqueue_stub.Clear()


@mock.patch.object(SeasonHelper, "get_current_season")
@mock.patch.object(DatafeedFMSAPI, "get_district_rankings")
def test_enqueue_default_year(
    district_rankings_mock,
    season_helper_mock,
    tasks_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
    ndb_stub,
) -> None:
    season_helper_mock.return_value = 2020
    district_rankings_mock.return_value = InstantFuture({})
    District(
        id="2020test",
        year=2020,
        abbreviation="test",
    ).put()
    resp = tasks_client.get("/tasks/math/enqueue/district_rankings_calc")
    assert resp.status_code == 200

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="default")
    assert len(tasks) == 2
    for task in tasks:
        task_resp = tasks_client.get(task.url)
        assert task_resp.status_code == 200

    taskqueue_stub.Clear()


def test_calc_no_district(tasks_client: Client) -> None:
    resp = tasks_client.get("/tasks/math/do/district_rankings_calc/2020ne")
    assert resp.status_code == 404


@pytest.mark.parametrize(
    "event_type,is_dcmp",
    [
        (EventType.REGIONAL, False),
        (EventType.DISTRICT_CMP, True),
        (EventType.DISTRICT_CMP_DIVISION, True),
    ],
)
@mock.patch.object(DistrictHelper, "calculate_rankings")
def test_calc(
    calc_mock: mock.Mock, event_type: EventType, is_dcmp: bool, tasks_client: Client
) -> None:
    District(
        id="2020ne",
        year=2020,
        abbreviation="ne",
    ).put()
    event = Event(
        id="2020event", year=2020, event_short="event", event_type_enum=event_type
    )
    calc_mock.return_value = {
        "frc254": DistrictRankingTeamTotal(
            event_points=[
                (
                    event,
                    TeamAtEventDistrictPoints(
                        event_key=event.key_name,
                        district_cmp=False,
                        qual_points=0,
                        elim_points=0,
                        alliance_points=0,
                        award_points=0,
                        total=0,
                    ),
                )
            ],
            point_total=0,
            tiebreakers=[],
            qual_scores=[],
            rookie_bonus=0,
            other_bonus=0,
        )
    }

    resp = tasks_client.get("/tasks/math/do/district_rankings_calc/2020ne")
    assert resp.status_code == 200
    assert b"Finished calculating rankings for: 2020ne" in resp.data

    district = District.get_by_id("2020ne")
    assert district is not None
    assert district.rankings == [
        DistrictRanking(
            rank=1,
            team_key="frc254",
            event_points=[
                TeamAtEventDistrictPoints(
                    event_key="2020event",
                    district_cmp=is_dcmp,
                    qual_points=0,
                    elim_points=0,
                    alliance_points=0,
                    award_points=0,
                    total=0,
                ),
            ],
            rookie_bonus=0,
            point_total=0,
        )
    ]


@mock.patch.object(DistrictHelper, "calculate_rankings")
def test_calc_no_output_in_taskqueue(
    calc_mock: mock.Mock, tasks_client: Client
) -> None:
    District(
        id="2020ne",
        year=2020,
        abbreviation="ne",
    ).put()
    calc_mock.return_value = {
        "frc254": DistrictRankingTeamTotal(
            event_points=[],
            point_total=0,
            tiebreakers=[],
            qual_scores=[],
            rookie_bonus=0,
            other_bonus=0,
        )
    }

    resp = tasks_client.get(
        "/tasks/math/do/district_rankings_calc/2020ne",
        headers={
            "X-Appengine-Taskname": "test",
        },
    )
    assert resp.status_code == 200
    assert resp.data == b""
