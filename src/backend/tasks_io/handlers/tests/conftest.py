import pytest
from google.appengine.ext import deferred, testbed
from werkzeug.test import Client

from backend.common.sitevars.fms_api_secrets import (
    ContentType as FMSApiSecretsContentType,
    FMSApiSecrets,
)


@pytest.fixture(autouse=True)
def always_drain_taskqueue(taskqueue_stub: testbed.taskqueue_stub.TaskQueueServiceStub):
    yield
    queues = ["datafeed", "cache-clearing", "post-update-hooks"]
    for queue in queues:
        tasks = taskqueue_stub.get_filtered_tasks(queue_names=queue)
        for task in tasks:
            if task.payload:
                deferred.run(task.payload)


@pytest.fixture
def tasks_client(gae_testbed, ndb_stub, memcache_stub, taskqueue_stub) -> Client:
    from backend.tasks_io.main import app

    return app.test_client()


@pytest.fixture(autouse=True)
def fms_api_secrets(ndb_stub):
    FMSApiSecrets.put(FMSApiSecretsContentType(username="zach", authkey="authkey"))
