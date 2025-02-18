import pytest
from google.appengine.ext import deferred, testbed
from werkzeug.test import Client

from backend.common.sitevars.fms_api_secrets import (
    ContentType as FMSApiSecretsContentType,
    FMSApiSecrets,
)


@pytest.fixture(autouse=True)
def always_drain_taskqueue(
    tasks_client: Client, taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub
):
    yield
    deferred_queues = ["datafeed", "cache-clearing", "post-update-hooks"]
    for queue in deferred_queues:
        tasks = taskqueue_stub.get_filtered_tasks(queue_names=queue)
        for task in tasks:
            if task.payload:
                deferred.run(task.payload)

    get_queues = ["default", "run-in-order"]
    for queue in get_queues:
        tasks = taskqueue_stub.get_filtered_tasks(queue_names=queue)
        for task in tasks:
            tasks_client.get(task.url)


@pytest.fixture(autouse=True)
def fms_api_secrets(ndb_stub):
    FMSApiSecrets.put(FMSApiSecretsContentType(username="zach", authkey="authkey"))
