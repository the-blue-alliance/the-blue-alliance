from typing import Optional
from unittest.mock import ANY, patch

import pytest
import requests
from fakeredis import FakeRedis

from backend.common.deferred.queues.rq_queue import RQTaskQueue
from backend.common.deferred.requests.rq_request import RQTaskRequest


def test_init(fake_redis_client: FakeRedis) -> None:
    name = "test_queue"
    default_service = "test-service"
    queue = RQTaskQueue(
        name, default_service=default_service, redis_client=fake_redis_client
    )
    assert queue.name == name
    assert queue.default_service == default_service


@pytest.mark.parametrize(
    "service, expected_service",
    [(None, "test-service"), ("new-service", "new-service")],
)
def test_task_request(
    fake_redis_client: FakeRedis, service: Optional[str], expected_service: str
) -> None:
    name = "test_queue"
    default_service = "test-service"
    queue = RQTaskQueue(
        name, default_service=default_service, redis_client=fake_redis_client
    )

    url = "https://thebluealliance.com"
    headers = {"X-Header": "abc"}
    body = bytes()

    request = queue._task_request(url, headers, body, service)
    assert type(request) is RQTaskRequest
    assert request.url is not None
    assert request.headers == headers
    assert request.body == body
    assert request.service == expected_service


def test_enqueue(fake_redis_client: FakeRedis) -> None:
    name = "test_queue"
    default_service = "test-service"
    queue = RQTaskQueue(
        name, default_service=default_service, redis_client=fake_redis_client
    )

    request = queue._task_request("", {}, bytes())

    with patch.object(queue._queue, "enqueue") as mock_enqueue:
        queue._enqueue(request)

    assert mock_enqueue.call_args == ((requests.post, ANY, ANY))
    assert mock_enqueue.call_args.kwargs["data"] == request.body
    assert mock_enqueue.call_args.kwargs["url"] == request.url
    assert mock_enqueue.call_args.kwargs["headers"] == request.headers
