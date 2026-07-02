import pytest
from freezegun import freeze_time
from google.appengine.ext import testbed
from werkzeug.test import Client

from backend.common.consts.insight_type import InsightType
from backend.common.models.district import District


def test_enqueue_bad_kind(tasks_cpu_client: Client) -> None:
    resp = tasks_cpu_client.get("/backend-tasks-b2/enqueue/math/insights/asdf/2023")
    assert resp.status_code == 404


def test_enqueue_bad_year(tasks_cpu_client: Client) -> None:
    resp = tasks_cpu_client.get("/backend-tasks-b2/enqueue/math/insights/matches/asdf")
    assert resp.status_code == 404


def test_enqueue(
    tasks_cpu_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:
    resp = tasks_cpu_client.get("/backend-tasks-b2/enqueue/math/insights/matches/2023")
    assert resp.status_code == 200

    tasks = tasks_cpu_client = taskqueue_stub.get_filtered_tasks(
        queue_names="backend-tasks"
    )
    assert len(tasks) == 1
    assert tasks[0].url == "/backend-tasks-b2/do/math/insights/matches/2023"


def test_enqueue_no_output_in_taskqueue(tasks_cpu_client: Client) -> None:
    resp = tasks_cpu_client.get(
        "/backend-tasks-b2/enqueue/math/insights/matches/2023",
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
    resp = tasks_cpu_client.get("/backend-tasks-b2/enqueue/math/insights/matches")
    assert resp.status_code == 200

    tasks = tasks_cpu_client = taskqueue_stub.get_filtered_tasks(
        queue_names="backend-tasks"
    )
    assert len(tasks) == 1
    assert tasks[0].url == "/backend-tasks-b2/do/math/insights/matches/2020"


def test_do_bad_kind(tasks_cpu_client: Client) -> None:
    resp = tasks_cpu_client.get("/backend-tasks-b2/do/math/insights/asdf/2023")
    assert resp.status_code == 404


def test_do_bad_year(tasks_cpu_client: Client) -> None:
    resp = tasks_cpu_client.get("/backend-tasks-b2/do/math/insights/matches/asdf")
    assert resp.status_code == 404


@pytest.mark.parametrize("insight_type", list(InsightType))  # pyre-ignore[6]
def test_calc(tasks_cpu_client: Client, insight_type: InsightType) -> None:
    resp = tasks_cpu_client.get(
        f"/backend-tasks-b2/do/math/insights/{insight_type}/2023"
    )
    assert resp.status_code == 200


def test_calc_no_output_in_taskqueue(tasks_cpu_client: Client) -> None:
    resp = tasks_cpu_client.get(
        "/backend-tasks-b2/do/math/insights/matches/2023",
        headers={
            "X-Appengine-Taskname": "test",
        },
    )
    assert resp.status_code == 200
    assert len(resp.data) == 0


def test_enqueue_district_insights(
    tasks_cpu_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:
    District(id="2026fim", year=2026, abbreviation="fim").put()
    District(id="2026ne", year=2026, abbreviation="ne").put()

    resp = tasks_cpu_client.get(
        "/backend-tasks-b2/enqueue/math/insights/districts/2026"
    )
    assert resp.status_code == 200

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="backend-tasks")
    assert len(tasks) == 2
    for task in tasks:
        assert task.url.startswith("/backend-tasks-b2/do/math/insights/districts/2026/")


@freeze_time("2026-03-01")
def test_enqueue_district_insights_defaults_to_current_season(
    tasks_cpu_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:
    District(id="2026fim", year=2026, abbreviation="fim").put()

    resp = tasks_cpu_client.get("/backend-tasks-b2/enqueue/math/insights/districts")
    assert resp.status_code == 200

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="backend-tasks")
    assert len(tasks) == 1
    for task in tasks:
        assert task.url.startswith("/backend-tasks-b2/do/math/insights/districts/2026/")


def test_enqueue_district_insights_no_output_in_taskqueue(
    tasks_cpu_client: Client,
) -> None:
    resp = tasks_cpu_client.get(
        "/backend-tasks-b2/enqueue/math/insights/districts",
        headers={"X-Appengine-Taskname": "test"},
    )
    assert resp.status_code == 200
    assert len(resp.data) == 0


def test_enqueue_district_insights_year_zero(
    tasks_cpu_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:
    from backend.common.consts.renamed_districts import RenamedDistricts

    expected_abbrevs = set(RenamedDistricts.get_latest_codes())

    resp = tasks_cpu_client.get("/backend-tasks-b2/enqueue/math/insights/districts/0")
    assert resp.status_code == 200

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="backend-tasks")
    assert len(tasks) == len(expected_abbrevs)
    enqueued_abbrevs = {task.url.split("/")[-1] for task in tasks}
    assert enqueued_abbrevs == expected_abbrevs
    for task in tasks:
        assert task.url.startswith("/backend-tasks-b2/do/math/insights/districts/0/")


def test_enqueue_district_insights_year_zero_no_output_in_taskqueue(
    tasks_cpu_client: Client,
) -> None:
    resp = tasks_cpu_client.get(
        "/backend-tasks-b2/enqueue/math/insights/districts/0",
        headers={"X-Appengine-Taskname": "test"},
    )
    assert resp.status_code == 200
    assert len(resp.data) == 0


def test_do_district_insights_for_abbreviation(tasks_cpu_client: Client) -> None:
    resp = tasks_cpu_client.get("/backend-tasks-b2/do/math/insights/districts/2026/fim")
    assert resp.status_code == 200


def test_do_district_insights_for_abbreviation_year_zero(
    tasks_cpu_client: Client,
) -> None:
    resp = tasks_cpu_client.get("/backend-tasks-b2/do/math/insights/districts/0/fim")
    assert resp.status_code == 200


def test_do_district_insights_for_abbreviation_no_output_in_taskqueue(
    tasks_cpu_client: Client,
) -> None:
    resp = tasks_cpu_client.get(
        "/backend-tasks-b2/do/math/insights/districts/2026/fim",
        headers={"X-Appengine-Taskname": "test"},
    )
    assert resp.status_code == 200
    assert len(resp.data) == 0
