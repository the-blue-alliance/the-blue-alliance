from google.cloud.tasks_v2 import AppEngineHttpRequest, AppEngineRouting
from google.cloud.tasks_v2.types import task as gct_task

from backend.common.deferred.requests.gcloud_service_request import (
    GCloudServiceTaskRequest,
)


def test_init():
    url = "https://thebluealliance.com"
    headers = {"a": "b"}
    body = bytes()
    service = "default"
    request = GCloudServiceTaskRequest(url, headers, body, service)

    assert request.headers == headers
    assert request.body == body
    assert request.service == service
    assert request.url is not None


def test_init_no_service():
    url = "https://thebluealliance.com"
    headers = {"a": "b"}
    body = bytes()
    request = GCloudServiceTaskRequest(url, headers, body)

    assert request.headers == headers
    assert request.body == body
    assert request.service is None
    assert request.url is not None


def test_url_partial():
    url = "/some/path/here?abc=def"
    service = "something-here"
    request = GCloudServiceTaskRequest(url, {}, bytes(), service)
    assert request.url == "/some/path/here?abc=def"


def test_url_full():
    url = "https://thebluealliance.com/some/path/here?abc=def"
    service = "py3-tasks-io"
    request = GCloudServiceTaskRequest(url, {}, bytes(), service)
    assert request.url == "/some/path/here?abc=def"


def test_proto_task():
    url = "https://thebluealliance.com"
    headers = {"a": "b"}
    body = bytes()
    request = GCloudServiceTaskRequest(url, headers, body)

    proto_task = request.proto_task
    assert type(proto_task) is gct_task.Task

    assert type(proto_task.app_engine_http_request) is AppEngineHttpRequest
    assert proto_task.app_engine_http_request.headers == headers
    assert proto_task.app_engine_http_request.body == body
    assert proto_task.app_engine_http_request.relative_uri == request.url

    assert proto_task.app_engine_http_request.app_engine_routing.service == ""


def test_proto_task_service():
    url = "https://thebluealliance.com"
    headers = {"a": "b"}
    body = bytes()
    service = "default"
    request = GCloudServiceTaskRequest(url, headers, body, service)

    proto_task = request.proto_task
    assert type(proto_task) is gct_task.Task

    assert type(proto_task.app_engine_http_request) is AppEngineHttpRequest
    assert proto_task.app_engine_http_request.headers == headers
    assert proto_task.app_engine_http_request.body == body
    assert proto_task.app_engine_http_request.relative_uri == request.url

    assert (
        type(proto_task.app_engine_http_request.app_engine_routing) is AppEngineRouting
    )
    assert proto_task.app_engine_http_request.app_engine_routing.service == service
