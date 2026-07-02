from google.appengine.ext import testbed
from werkzeug.test import Client

from backend.common.models.insight_v2 import InsightV2


def test_do_empty_returns_200(tasks_cpu_client: Client, ndb_stub) -> None:
    resp = tasks_cpu_client.get("/backend-tasks-b2/do/math/insights_v2/2024")
    assert resp.status_code == 200
    assert InsightV2.query().count() == 0


def test_do_writes_all_insights(
    tasks_cpu_client: Client, ndb_stub, test_data_importer
) -> None:
    test_data_importer.import_event(
        __file__, "../../../common/helpers/tests/data/2024nytr.json"
    )
    test_data_importer.import_award_list(
        __file__, "../../../common/helpers/tests/data/2024nytr_awards.json"
    )

    resp = tasks_cpu_client.get("/backend-tasks-b2/do/math/insights_v2/2024")
    assert resp.status_code == 200

    insights = InsightV2.query().fetch()
    assert len(insights) == 1


def test_enqueue(
    tasks_cpu_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:
    resp = tasks_cpu_client.get("/backend-tasks-b2/enqueue/math/insights_v2/2024")
    assert resp.status_code == 200

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="backend-tasks")
    assert len(tasks) == 1
    assert tasks[0].url == "/backend-tasks-b2/do/math/insights_v2/2024"


def test_enqueue_all(
    tasks_cpu_client: Client,
    taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub,
) -> None:
    resp = tasks_cpu_client.get("/backend-tasks-b2/enqueue/math/insights_v2/all")
    assert resp.status_code == 200

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="backend-tasks")
    assert len(tasks) >= 1
