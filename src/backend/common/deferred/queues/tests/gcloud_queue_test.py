from typing import Optional
from unittest.mock import patch

import pytest
from google.cloud import tasks_v2

from backend.common.deferred.conftest import FakeCloudTasksClient
from backend.common.deferred.queues.gcloud_queue import GCloudTaskQueue
from backend.common.deferred.requests.gcloud_http_request import (
    GCloudHttpTaskRequest,
    GCloudHttpTaskRequestConfiguration,
)
from backend.common.deferred.requests.gcloud_service_request import (
    GCloudServiceTaskRequest,
)


def test_init(fake_gcloud_client: FakeCloudTasksClient) -> None:
    name = "test_queue"
    queue = GCloudTaskQueue(name, gcloud_client=fake_gcloud_client)
    assert queue.name == name
    assert queue.http_request_configuration is None


def test_init_http_request_configuration(
    fake_gcloud_client: FakeCloudTasksClient,
) -> None:
    name = "test_queue"
    http_request_configuration = GCloudHttpTaskRequestConfiguration(
        base_url="https://thebluealliance.com"
    )
    queue = GCloudTaskQueue(
        name,
        http_request_configuration=http_request_configuration,
        gcloud_client=fake_gcloud_client,
    )
    assert queue.name == name
    assert queue.http_request_configuration == http_request_configuration


@pytest.mark.parametrize("service", [None, "test-service"])
def test_task_request(
    fake_gcloud_client: FakeCloudTasksClient, service: Optional[str]
) -> None:
    queue = GCloudTaskQueue("test_queue", gcloud_client=fake_gcloud_client)

    url = "https://thebluealliance.com"
    headers = {"X-Header": "abc"}
    body = bytes()

    request = queue._task_request(url, headers, body, service)
    assert type(request) is GCloudServiceTaskRequest
    assert request.url is not None
    assert request.headers == headers
    assert request.body == body
    assert request.service == service


def test_task_request_http_request_configuration(
    fake_gcloud_client: FakeCloudTasksClient,
) -> None:
    http_request_configuration = GCloudHttpTaskRequestConfiguration(
        base_url="https://thebluealliance.com"
    )
    queue = GCloudTaskQueue(
        "test_queue",
        http_request_configuration=http_request_configuration,
        gcloud_client=fake_gcloud_client,
    )

    url = "https://thebluealliance.com"
    headers = {"X-Header": "abc"}
    body = bytes()
    service = "service"

    request = queue._task_request(url, headers, body, service)
    assert type(request) is GCloudHttpTaskRequest
    assert request.configuration == http_request_configuration
    assert request.url is not None
    assert request.headers == headers
    assert request.body == body
    assert request.service is None


def test_enqueue(fake_gcloud_client: FakeCloudTasksClient) -> None:
    queue_name = "test_queue"
    queue = GCloudTaskQueue(queue_name, gcloud_client=fake_gcloud_client)
    request = queue._task_request("", {}, bytes())

    with patch.object(fake_gcloud_client, "create_task") as mock_create_task:
        queue._enqueue(request)

    proto_request = mock_create_task.call_args.kwargs["request"]
    assert type(proto_request) is tasks_v2.CreateTaskRequest
    assert proto_request.parent == queue_name
    assert proto_request.task == request.proto_task
