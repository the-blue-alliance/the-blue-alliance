from unittest import mock

from freezegun import freeze_time
from google.appengine.ext import testbed
from werkzeug.test import Client

from backend.common.futures import InstantFuture
from backend.common.models.district import District
from backend.common.models.district_advancement import TeamDistrictAdvancement
from backend.tasks_io.datafeeds.datafeed_fms_api import DatafeedFMSAPI
from backend.tasks_io.datafeeds.parsers.fms_api.fms_api_district_rankings_parser import (
    TParsedDistrictRankings,
)


def test_district_list_bad_year(tasks_client: Client) -> None:
    resp = tasks_client.get("/backend-tasks/get/district_list/asdf")
    assert resp.status_code == 404


@mock.patch.object(DatafeedFMSAPI, "get_district_list")
def test_district_list_get_year(api_mock, tasks_client: Client) -> None:
    api_mock.return_value = InstantFuture(
        [District(id="2020ne", year=2020, abbreviation="ne")]
    )

    resp = tasks_client.get("/backend-tasks/get/district_list/2020")
    assert resp.status_code == 200
    assert len(resp.data) > 0

    # Ensure we created models
    assert District.get_by_id("2020ne") is not None


@mock.patch.object(DatafeedFMSAPI, "get_district_list")
def test_district_list_get_year_no_output_in_taskqueue(
    api_mock, tasks_client: Client
) -> None:
    api_mock.return_value = InstantFuture(
        [District(id="2020ne", year=2020, abbreviation="ne")]
    )

    resp = tasks_client.get(
        "/backend-tasks/get/district_list/2020",
        headers={"X-Appengine-Taskname": "test"},
    )
    assert resp.status_code == 200
    assert len(resp.data) == 0

    # Ensure we created models
    assert District.get_by_id("2020ne") is not None


def test_district_rankings_bad_key(tasks_client: Client) -> None:
    resp = tasks_client.get("/backend-tasks/get/district_rankings/asdf")
    assert resp.status_code == 404


def test_district_rankings_no_district(tasks_client: Client) -> None:
    resp = tasks_client.get("/backend-tasks/get/district_rankings/2020ne")
    assert resp.status_code == 404


@mock.patch.object(DatafeedFMSAPI, "get_district_rankings")
def test_district_rankings(api_mock, tasks_client: Client) -> None:
    District(id="2020ne", year=2020, abbreviation="ne").put()
    advancement = {"frc254": TeamDistrictAdvancement(dcmp=True, cmp=True)}
    adjustments = {"frc254": 5}
    api_mock.return_value = InstantFuture(
        TParsedDistrictRankings(
            advancement=advancement, adjustments=adjustments, api_team_data={}
        )
    )

    resp = tasks_client.get(
        "/backend-tasks/get/district_rankings/2020ne",
    )
    assert resp.status_code == 200
    assert len(resp.data) > 0

    # Advancement was saved; adjustments were not touched by this endpoint
    d = District.get_by_id("2020ne")
    assert d is not None
    assert d.advancement == advancement
    assert d.adjustments is None


@mock.patch.object(DatafeedFMSAPI, "get_district_rankings")
def test_district_rankings_no_output_in_taskqueue(
    api_mock, tasks_client: Client
) -> None:
    District(id="2020ne", year=2020, abbreviation="ne").put()
    advancement = {"frc254": TeamDistrictAdvancement(dcmp=True, cmp=True)}
    adjustments = {"frc254": 5}
    api_mock.return_value = InstantFuture(
        TParsedDistrictRankings(
            advancement=advancement, adjustments=adjustments, api_team_data={}
        )
    )

    resp = tasks_client.get(
        "/backend-tasks/get/district_rankings/2020ne",
        headers={"X-Appengine-Taskname": "test"},
    )
    assert resp.status_code == 200
    assert len(resp.data) == 0

    d = District.get_by_id("2020ne")
    assert d is not None
    assert d.advancement == advancement
    assert d.adjustments is None


def test_district_adjustments_bad_key(tasks_client: Client) -> None:
    resp = tasks_client.get("/backend-tasks/get/district_adjustments/asdf")
    assert resp.status_code == 404


def test_district_adjustments_no_district(tasks_client: Client) -> None:
    resp = tasks_client.get("/backend-tasks/get/district_adjustments/2020ne")
    assert resp.status_code == 404


@mock.patch.object(DatafeedFMSAPI, "get_district_rankings")
def test_district_adjustments(api_mock, tasks_client: Client) -> None:
    District(id="2020ne", year=2020, abbreviation="ne").put()
    advancement = {"frc254": TeamDistrictAdvancement(dcmp=True, cmp=True)}
    adjustments = {"frc254": 5}
    api_mock.return_value = InstantFuture(
        TParsedDistrictRankings(
            advancement=advancement, adjustments=adjustments, api_team_data={}
        )
    )

    resp = tasks_client.get(
        "/backend-tasks/get/district_adjustments/2020ne",
    )
    assert resp.status_code == 200
    assert len(resp.data) > 0

    # Adjustments were saved; advancement was not touched by this endpoint
    d = District.get_by_id("2020ne")
    assert d is not None
    assert d.adjustments == adjustments
    assert d.advancement is None


@mock.patch.object(DatafeedFMSAPI, "get_district_rankings")
def test_district_adjustments_no_output_in_taskqueue(
    api_mock, tasks_client: Client
) -> None:
    District(id="2020ne", year=2020, abbreviation="ne").put()
    advancement = {"frc254": TeamDistrictAdvancement(dcmp=True, cmp=True)}
    adjustments = {"frc254": 5}
    api_mock.return_value = InstantFuture(
        TParsedDistrictRankings(
            advancement=advancement, adjustments=adjustments, api_team_data={}
        )
    )

    resp = tasks_client.get(
        "/backend-tasks/get/district_adjustments/2020ne",
        headers={"X-Appengine-Taskname": "test"},
    )
    assert resp.status_code == 200
    assert len(resp.data) == 0

    d = District.get_by_id("2020ne")
    assert d is not None
    assert d.adjustments == adjustments
    assert d.advancement is None


@freeze_time("2020-4-1")
def test_enqueue_district_advancement_no_districts(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    resp = tasks_client.get("/tasks/enqueue/district_advancement/2020")
    assert resp.status_code == 200
    assert resp.data == b"Enqueued for: []"

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="default")
    assert len(tasks) == 0


@freeze_time("2020-4-1")
def test_enqueue_district_advancement_with_districts(
    tasks_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
    ndb_stub,
) -> None:
    District(id="2020ne", year=2020, abbreviation="ne").put()
    District(id="2020fim", year=2020, abbreviation="fim").put()

    resp = tasks_client.get("/tasks/enqueue/district_advancement/2020")
    assert resp.status_code == 200

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="default")
    assert len(tasks) == 2
    urls = sorted(task.url for task in tasks)
    assert urls == [
        "/backend-tasks/get/district_rankings/2020fim",
        "/backend-tasks/get/district_rankings/2020ne",
    ]
    taskqueue_stub.Clear()


@freeze_time("2020-4-1")
def test_enqueue_district_advancement_default_year(
    tasks_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
    ndb_stub,
) -> None:
    District(id="2020ne", year=2020, abbreviation="ne").put()

    resp = tasks_client.get("/tasks/enqueue/district_advancement")
    assert resp.status_code == 200

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="default")
    assert len(tasks) == 1
    taskqueue_stub.Clear()


@freeze_time("2020-4-1")
def test_enqueue_district_advancement_no_output_in_taskqueue(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
) -> None:
    resp = tasks_client.get(
        "/tasks/enqueue/district_advancement/2020",
        headers={"X-Appengine-Taskname": "test"},
    )
    assert resp.status_code == 200
    assert resp.data == b""
