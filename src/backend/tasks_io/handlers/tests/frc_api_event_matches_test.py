import datetime
import json
from typing import Dict, Optional
from unittest import mock

import pytest
from freezegun import freeze_time
from google.appengine.ext import ndb, testbed
from werkzeug.test import Client

from backend.common.consts.comp_level import CompLevel
from backend.common.consts.event_type import EventType
from backend.common.futures import InstantFuture
from backend.common.models.event import Event
from backend.common.models.match import Match
from backend.tasks_io.datafeeds.datafeed_fms_api import DatafeedFMSAPI


def create_event(official: bool, remap_teams: Optional[Dict[str, str]] = None) -> None:
    Event(
        id="2020nyny",
        year=2020,
        event_short="nyny",
        event_type_enum=EventType.REGIONAL,
        start_date=datetime.datetime(2020, 4, 1),
        end_date=datetime.datetime(2020, 4, 2),
        official=official,
        remap_teams=remap_teams,
    ).put()


def test_enqueue_bad_when(tasks_client: Client) -> None:
    resp = tasks_client.get("/tasks/enqueue/fmsapi_matches/asdf")
    assert resp.status_code == 404


@freeze_time("2020-4-1")
def test_enqueue_current(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    create_event(official=True)
    resp = tasks_client.get("/tasks/enqueue/fmsapi_matches/now")
    assert resp.status_code == 200
    assert len(resp.data) > 0

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="datafeed")
    assert len(tasks) == 1

    expected_keys = ["2020nyny"]
    assert [f"/tasks/get/fmsapi_matches/{k}" for k in expected_keys] == [
        t.url for t in tasks
    ]


@freeze_time("2020-4-1")
def test_enqueue_current_skips_unofficial(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    create_event(official=False)
    resp = tasks_client.get("/tasks/enqueue/fmsapi_matches/now")
    assert resp.status_code == 200
    assert len(resp.data) > 0

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="datafeed")
    assert len(tasks) == 0


@freeze_time("2020-4-1")
def test_enqueue_current_no_output_in_taskqueue(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    resp = tasks_client.get(
        "/tasks/enqueue/fmsapi_matches/now",
        headers={"X-Appengine-Taskname": "test"},
    )
    assert resp.status_code == 200
    assert len(resp.data) == 0

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="datafeed")
    assert len(tasks) == 0


def test_enqueue_explicit_year(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    create_event(official=True)
    resp = tasks_client.get("/tasks/enqueue/fmsapi_matches/2020")
    assert resp.status_code == 200

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="datafeed")
    assert len(tasks) == 1
    assert tasks[0].url == "/tasks/get/fmsapi_matches/2020nyny"


def test_enqueue_explicit_year_skips_unofficial(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    create_event(official=False)
    resp = tasks_client.get("/tasks/enqueue/fmsapi_matches/2020")
    assert resp.status_code == 200

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="datafeed")
    assert len(tasks) == 0


def test_get_bad_key(tasks_client: Client) -> None:
    resp = tasks_client.get("/tasks/get/fmsapi_matches/asdf")
    assert resp.status_code == 404


@pytest.mark.filterwarnings("ignore::ResourceWarning")
def test_get_no_event(tasks_client: Client) -> None:
    resp = tasks_client.get("/tasks/get/fmsapi_matches/2020nyny")
    assert resp.status_code == 404


@mock.patch.object(DatafeedFMSAPI, "get_event_matches")
def test_get_no_matches(fmsapi_matches_mock, tasks_client: Client) -> None:
    create_event(official=True)
    fmsapi_matches_mock.return_value = InstantFuture([])

    resp = tasks_client.get("/tasks/get/fmsapi_matches/2020nyny")
    assert resp.status_code == 200
    assert len(resp.data) > 0


@mock.patch.object(DatafeedFMSAPI, "get_event_matches")
def test_get_no_matches_no_output_in_taskqueue(
    fmsapi_matches_mock, tasks_client: Client
) -> None:
    create_event(official=True)
    fmsapi_matches_mock.return_value = InstantFuture([])

    resp = tasks_client.get(
        "/tasks/get/fmsapi_matches/2020nyny",
        headers={"X-Appengine-Taskname": "test"},
    )
    assert resp.status_code == 200
    assert len(resp.data) == 0


@mock.patch.object(DatafeedFMSAPI, "get_event_matches")
def test_get(
    fmsapi_matches_mock,
    tasks_client: Client,
) -> None:
    create_event(official=True)
    matches = [
        Match(
            id="2020nyny_qm1",
            event=ndb.Key(Event, "2020nyny"),
            comp_level=CompLevel.QM,
            set_number=1,
            match_number=1,
            year=2020,
            alliances_json=json.dumps({"red": {"score": "-1"}, "blue": {"score": -1}}),
        )
    ]

    fmsapi_matches_mock.return_value = InstantFuture(matches)

    resp = tasks_client.get("/tasks/get/fmsapi_matches/2020nyny")
    assert resp.status_code == 200
    assert len(resp.data) > 0

    # Make sure we write objects
    assert Match.get_by_id("2020nyny_qm1") is not None


@pytest.mark.filterwarnings("ignore:divide by zero")
@mock.patch.object(DatafeedFMSAPI, "get_event_matches")
def test_get_remap_teams(
    fmsapi_matches_mock,
    tasks_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:
    create_event(official=True, remap_teams={"frc254": "frc9000"})
    matches = [
        Match(
            id="2020nyny_qm1",
            event=ndb.Key(Event, "2020nyny"),
            comp_level=CompLevel.QM,
            set_number=1,
            match_number=1,
            year=2020,
            alliances_json=json.dumps(
                {
                    "red": {"score": "-1", "teams": ["frc254"]},
                    "blue": {"score": -1, "teams": []},
                }
            ),
            team_key_names=["frc254"],
        )
    ]

    fmsapi_matches_mock.return_value = InstantFuture(matches)

    resp = tasks_client.get("/tasks/get/fmsapi_matches/2020nyny")
    assert resp.status_code == 200
    assert len(resp.data) > 0

    # Make sure we write objects
    m = Match.get_by_id("2020nyny_qm1")
    assert m is not None
    assert m.team_key_names == ["frc9000"]


@mock.patch.object(DatafeedFMSAPI, "get_event_matches")
def test_delete_invalid(
    fmsapi_matches_mock,
    tasks_client: Client,
) -> None:
    create_event(official=True)
    # Red wins both matches, the third match is invalid
    matches = [
        Match(
            id="2020nyny_f1m1",
            event=ndb.Key(Event, "2020nyny"),
            comp_level=CompLevel.F,
            set_number=1,
            match_number=1,
            year=2020,
            alliances_json=json.dumps({"red": {"score": 20}, "blue": {"score": 10}}),
        ),
        Match(
            id="2020nyny_f1m2",
            event=ndb.Key(Event, "2020nyny"),
            comp_level=CompLevel.F,
            set_number=1,
            match_number=2,
            year=2020,
            alliances_json=json.dumps({"red": {"score": 20}, "blue": {"score": 10}}),
        ),
    ]

    fmsapi_matches_mock.return_value = InstantFuture(matches)

    # Add existing matches
    [m.put() for m in matches]
    Match(
        id="2020nyny_f1m3",
        event=ndb.Key(Event, "2020nyny"),
        comp_level=CompLevel.F,
        set_number=1,
        match_number=3,
        year=2020,
        alliances_json=json.dumps({"red": {"score": "-1"}, "blue": {"score": -1}}),
    ).put()

    resp = tasks_client.get("/tasks/get/fmsapi_matches/2020nyny")
    assert resp.status_code == 200
    assert len(resp.data) > 0

    # Make sure we write objects
    assert Match.get_by_id("2020nyny_f1m1") is not None
    assert Match.get_by_id("2020nyny_f1m2") is not None
    # Make sure we delete objects
    assert Match.get_by_id("2020nyny_f1m3") is None


@mock.patch.object(DatafeedFMSAPI, "get_event_matches")
def test_no_delete_invalid(
    fmsapi_matches_mock,
    tasks_client: Client,
) -> None:
    create_event(official=True)
    # Red and blue win one match each, we need to keep the third match
    matches = [
        Match(
            id="2020nyny_f1m1",
            event=ndb.Key(Event, "2020nyny"),
            comp_level=CompLevel.F,
            set_number=1,
            match_number=1,
            year=2020,
            alliances_json=json.dumps({"red": {"score": 20}, "blue": {"score": 10}}),
        ),
        Match(
            id="2020nyny_f1m2",
            event=ndb.Key(Event, "2020nyny"),
            comp_level=CompLevel.F,
            set_number=1,
            match_number=2,
            year=2020,
            alliances_json=json.dumps({"red": {"score": 10}, "blue": {"score": 20}}),
        ),
    ]

    fmsapi_matches_mock.return_value = InstantFuture(matches)

    # Add existing matches
    [m.put() for m in matches]
    Match(
        id="2020nyny_f1m3",
        event=ndb.Key(Event, "2020nyny"),
        comp_level=CompLevel.F,
        set_number=1,
        match_number=3,
        year=2020,
        alliances_json=json.dumps({"red": {"score": "-1"}, "blue": {"score": -1}}),
    ).put()

    resp = tasks_client.get("/tasks/get/fmsapi_matches/2020nyny")
    assert resp.status_code == 200
    assert len(resp.data) > 0

    # Make sure we write objects
    assert Match.get_by_id("2020nyny_f1m1") is not None
    assert Match.get_by_id("2020nyny_f1m2") is not None
    assert Match.get_by_id("2020nyny_f1m3") is not None
