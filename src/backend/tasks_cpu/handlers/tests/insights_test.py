import pytest
from freezegun import freeze_time
from google.appengine.ext import testbed
from werkzeug.test import Client

from backend.common.consts.insight_type import InsightType


def test_enqueue_bad_kind(tasks_cpu_client: Client) -> None:
    resp = tasks_cpu_client.get("/backend-tasks-b2/math/enqueue/insights/asdf/2023")
    assert resp.status_code == 404


def test_enqueue_bad_year(tasks_cpu_client: Client) -> None:
    resp = tasks_cpu_client.get("/backend-tasks-b2/math/enqueue/insights/matches/asdf")
    assert resp.status_code == 404


def test_enqueue(
    tasks_cpu_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:
    resp = tasks_cpu_client.get("/backend-tasks-b2/math/enqueue/insights/matches/2023")
    assert resp.status_code == 200

    tasks = tasks_cpu_client = taskqueue_stub.get_filtered_tasks(
        queue_names="backend-tasks"
    )
    assert len(tasks) == 1
    assert tasks[0].url == "/backend-tasks-b2/math/do/insights/matches/2023"


def test_enqueue_no_output_in_taskqueue(tasks_cpu_client: Client) -> None:
    resp = tasks_cpu_client.get(
        "/backend-tasks-b2/math/enqueue/insights/matches/2023",
        headers={
            "X-Appengine-Taskname": "test",
        },
    )
    assert resp.status_code == 200
    assert len(resp.data) == 0


@freeze_time("2020-04-01")
def test_enqueue_defaults_to_current_season(
    tasks_cpu_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:
    resp = tasks_cpu_client.get("/backend-tasks-b2/math/enqueue/insights/matches")
    assert resp.status_code == 200

    tasks = tasks_cpu_client = taskqueue_stub.get_filtered_tasks(
        queue_names="backend-tasks"
    )
    assert len(tasks) == 1
    assert tasks[0].url == "/backend-tasks-b2/math/do/insights/matches/2020"


def test_do_bad_kind(tasks_cpu_client: Client) -> None:
    resp = tasks_cpu_client.get("/backend-tasks-b2/math/do/insights/asdf/2023")
    assert resp.status_code == 404


def test_do_bad_year(tasks_cpu_client: Client) -> None:
    resp = tasks_cpu_client.get("/backend-tasks-b2/math/do/insights/matches/asdf")
    assert resp.status_code == 404


@pytest.mark.parametrize("insight_type", list(InsightType))  # pyre-ignore[6]
def test_calc(tasks_cpu_client: Client, insight_type: InsightType) -> None:
    resp = tasks_cpu_client.get(
        f"/backend-tasks-b2/math/do/insights/{insight_type}/2023"
    )
    assert resp.status_code == 200


def test_calc_no_output_in_taskqueue(tasks_cpu_client: Client) -> None:
    resp = tasks_cpu_client.get(
        "/backend-tasks-b2/math/do/insights/matches/2023",
        headers={
            "X-Appengine-Taskname": "test",
        },
    )
    assert resp.status_code == 200
    assert len(resp.data) == 0
