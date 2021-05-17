from backend.common.deferred.requests.rq_request import RQTaskRequest


def test_init():
    url = "https://thebluealliance.com"
    headers = {"a": "b"}
    body = bytes()
    service = "default"
    request = RQTaskRequest(url, headers, body, service)

    assert request.headers == headers
    assert request.body == body
    assert request.service == service
    assert request.url is not None


def test_url_service_fallback():
    url = "/some/path/here?abc=def"
    service = "something-here"
    request = RQTaskRequest(url, {}, bytes(), service)
    assert request.url == "http://localhost:8081/some/path/here?abc=def"


def test_url_service():
    url = "/some/path/here?abc=def"
    service = "py3-tasks-io"
    request = RQTaskRequest(url, {}, bytes(), service)
    assert request.url == "http://localhost:8084/some/path/here?abc=def"
