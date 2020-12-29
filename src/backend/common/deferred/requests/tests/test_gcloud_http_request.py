from google.cloud.tasks_v2 import HttpRequest
from google.cloud.tasks_v2.types import task as gct_task

from backend.common.deferred.requests.gcloud_http_request import (
    GCloudHttpTaskRequest,
    GCloudHttpTaskRequestConfiguration,
)


def test_init():
    configuration = GCloudHttpTaskRequestConfiguration(
        base_url="http://1d03c3c73356.ngrok.io"
    )
    url = "https://thebluealliance.com"
    headers = {"a": "b"}
    body = bytes()
    request = GCloudHttpTaskRequest(configuration, url, headers, body)

    assert request.configuration == configuration
    assert request.headers == headers
    assert request.body == body
    assert request.service is None
    assert request.url is not None


def test_url_partial():
    configuration = GCloudHttpTaskRequestConfiguration(
        base_url="http://1d03c3c73356.ngrok.io"
    )
    url = "/some/path/here?abc=def"
    headers = {"a": "b"}
    body = bytes()
    request = GCloudHttpTaskRequest(configuration, url, headers, body)
    assert request.url == "http://1d03c3c73356.ngrok.io/some/path/here?abc=def"


def test_url_full():
    configuration = GCloudHttpTaskRequestConfiguration(
        base_url="http://1d03c3c73356.ngrok.io"
    )
    url = "https://thebluealliance.com/some/path/here?abc=def"
    headers = {"a": "b"}
    body = bytes()
    request = GCloudHttpTaskRequest(configuration, url, headers, body)
    assert request.url == "http://1d03c3c73356.ngrok.io/some/path/here?abc=def"


def test_proto_task():
    configuration = GCloudHttpTaskRequestConfiguration(
        base_url="http://1d03c3c73356.ngrok.io"
    )
    url = "/some/path/here?abc=def"
    headers = {"a": "b"}
    body = bytes()
    request = GCloudHttpTaskRequest(configuration, url, headers, body)

    proto_task = request.proto_task
    assert type(proto_task) is gct_task.Task

    assert type(proto_task.http_request) is HttpRequest
    assert proto_task.http_request.headers == headers
    assert proto_task.http_request.body == body
    assert proto_task.http_request.url == request.url
