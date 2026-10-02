from typing import Any, cast
from unittest.mock import Mock, patch
from wsgiref.types import WSGIApplication

import pytest
from _pytest.monkeypatch import MonkeyPatch
from flask import Flask
from werkzeug.test import create_environ, run_wsgi_app
from werkzeug.wrappers import Request

from backend.common import middleware
from backend.common.environment import Environment
from backend.common.logging import logging_context
from backend.common.middleware import (
    _set_secret_key,
    AfterResponseMiddleware,
    AppspotRedirectMiddleware,
    install_middleware,
    TraceRequestMiddleware,
)
from backend.common.profiler import trace_context
from backend.common.run_after_response import response_context, run_after_response


def test_AppspotRedirectMiddleware_init(app: Flask) -> None:
    middleware = AppspotRedirectMiddleware(app)
    assert middleware.app is app


def test_AppspotRedirectMiddleware_redirect_appspot(app: Flask) -> None:
    middleware = cast(WSGIApplication, AppspotRedirectMiddleware(app))

    # Test redirect for appspot.com host
    environ = create_environ(
        path="/team/254",
        query_string="year=2023",
        base_url="https://tbatv-prod-hrd.appspot.com",
    )
    _, status, headers = run_wsgi_app(middleware, environ, buffered=True)

    assert status == "301 MOVED PERMANENTLY"
    location_header = next((v for k, v in headers if k == "Location"), None)
    assert location_header == "https://www.thebluealliance.com/team/254?year=2023"


def test_AppspotRedirectMiddleware_redirect_appspot_no_query(app: Flask) -> None:
    middleware = cast(WSGIApplication, AppspotRedirectMiddleware(app))

    # Test redirect for appspot.com host without query string
    environ = create_environ(
        path="/events", base_url="https://tbatv-prod-hrd.appspot.com"
    )
    _, status, headers = run_wsgi_app(middleware, environ, buffered=True)

    assert status == "301 MOVED PERMANENTLY"
    location_header = next((v for k, v in headers if k == "Location"), None)
    assert location_header == "https://www.thebluealliance.com/events"


def test_AppspotRedirectMiddleware_redirect_www_appspot(app: Flask) -> None:
    middleware = cast(WSGIApplication, AppspotRedirectMiddleware(app))

    # Test redirect for www.tbatv-prod-hrd.appspot.com host
    environ = create_environ(
        path="/team/254",
        query_string="year=2023",
        base_url="https://www.tbatv-prod-hrd.appspot.com",
    )
    _, status, headers = run_wsgi_app(middleware, environ, buffered=True)

    assert status == "301 MOVED PERMANENTLY"
    location_header = next((v for k, v in headers if k == "Location"), None)
    assert location_header == "https://www.thebluealliance.com/team/254?year=2023"


def test_AppspotRedirectMiddleware_redirect_www_appspot_no_query(app: Flask) -> None:
    middleware = cast(WSGIApplication, AppspotRedirectMiddleware(app))

    # Test redirect for www.tbatv-prod-hrd.appspot.com host without query string
    environ = create_environ(
        path="/events", base_url="https://www.tbatv-prod-hrd.appspot.com"
    )
    _, status, headers = run_wsgi_app(middleware, environ, buffered=True)

    assert status == "301 MOVED PERMANENTLY"
    location_header = next((v for k, v in headers if k == "Location"), None)
    assert location_header == "https://www.thebluealliance.com/events"


def test_AppspotRedirectMiddleware_no_redirect_thebluealliance(app: Flask) -> None:
    middleware = cast(WSGIApplication, AppspotRedirectMiddleware(app))

    @app.route("/test")
    def test_handler():
        return "Hello!"

    # Test no redirect for thebluealliance.com host
    environ = create_environ(path="/test", base_url="https://thebluealliance.com")
    _, status, headers = run_wsgi_app(middleware, environ, buffered=True)

    assert status == "200 OK"
    location_header = next((v for k, v in headers if k == "Location"), None)
    assert location_header is None


def test_AppspotRedirectMiddleware_no_redirect_localhost(app: Flask) -> None:
    middleware = cast(WSGIApplication, AppspotRedirectMiddleware(app))

    @app.route("/test")
    def test_handler():
        return "Hello!"

    # Test no redirect for localhost
    environ = create_environ(path="/test", base_url="http://localhost:8080")
    _, status, headers = run_wsgi_app(middleware, environ, buffered=True)

    assert status == "200 OK"
    location_header = next((v for k, v in headers if k == "Location"), None)
    assert location_header is None


def test_AppspotRedirectMiddleware_no_redirect_ah_path(app: Flask) -> None:
    middleware = cast(WSGIApplication, AppspotRedirectMiddleware(app))

    @app.route("/_ah/warmup")
    def warmup_handler():
        return "warmup ok"

    # Test no redirect for /_ah/ paths on appspot host
    environ = create_environ(
        path="/_ah/warmup", base_url="https://tbatv-prod-hrd.appspot.com"
    )
    _, status, headers = run_wsgi_app(middleware, environ, buffered=True)

    assert status == "200 OK"
    location_header = next((v for k, v in headers if k == "Location"), None)
    assert location_header is None


def test_TraceRequestMiddleware_init(app: Flask) -> None:
    middleware = TraceRequestMiddleware(app)
    assert middleware.app is app


def test_TraceRequestMiddleware_callable(app: Flask) -> None:
    middleware = TraceRequestMiddleware(app)

    def start_response(status, headers):
        pass

    environ = create_environ(path="/", base_url="http://localhost")
    middleware(environ, start_response)

    assert isinstance(trace_context.request, Request)
    assert isinstance(logging_context.request, Request)
    assert hasattr(logging_context.request, "logging_context")
    assert isinstance(logging_context.request.logging_context, dict)


def test_AfterResponseMiddleware_init(app: Flask) -> None:
    middleware = AfterResponseMiddleware(app)
    assert middleware.app is app


def test_AfterResponseMiddleware_callable(app: Flask) -> None:
    middleware = cast(WSGIApplication, AfterResponseMiddleware(app))
    callback1 = Mock()
    callback2 = Mock()

    @app.route("/0")
    def test_handler0():
        return "Hello!"

    @app.route("/1")
    def test_handler1():
        run_after_response(callback1)
        return "Hello!"

    @app.route("/2")
    def test_handler2():
        run_after_response(callback2)
        return "Hello!"

    # Test no callback.
    callback1.assert_not_called()
    callback2.assert_not_called()
    environ = create_environ(path="/0", base_url="http://localhost")
    run_wsgi_app(middleware, environ, buffered=True)
    callback1.assert_not_called()
    callback2.assert_not_called()

    # Test first callback.
    callback1.assert_not_called()
    callback2.assert_not_called()
    environ = create_environ(path="/1", base_url="http://localhost")
    run_wsgi_app(middleware, environ, buffered=True)
    callback1.assert_called_once()
    callback2.assert_not_called()

    # Ensure a second call doesn't call the first callback again.
    callback1.assert_called_once()
    callback2.assert_not_called()
    environ = create_environ(path="/2", base_url="http://localhost")
    run_wsgi_app(middleware, environ, buffered=True)
    callback1.assert_called_once()
    callback2.assert_called_once()
    assert not hasattr(response_context, "request")


def test_AfterResponseMiddleware_exception_in_app() -> None:
    failing_app = Mock(side_effect=RuntimeError("WSGI error"))
    middleware_app = cast(WSGIApplication, AfterResponseMiddleware(failing_app))

    environ = create_environ(path="/error", base_url="http://localhost")
    with patch("backend.common.middleware.send_traces") as mock_send_traces:
        with pytest.raises(RuntimeError, match="WSGI error"):
            run_wsgi_app(middleware_app, environ, buffered=True)

        mock_send_traces.assert_called_once()
        assert not hasattr(response_context, "request")


def test_AfterResponseMiddleware_cleans_up_on_flask_500(app: Flask) -> None:
    middleware_app = cast(WSGIApplication, AfterResponseMiddleware(app))

    @app.route("/flask_error")
    def test_handler_error():
        raise RuntimeError("Flask view crashed")

    environ = create_environ(path="/flask_error", base_url="http://localhost")
    _, status, _ = run_wsgi_app(middleware_app, environ, buffered=True)

    assert status == "500 INTERNAL SERVER ERROR"
    assert not hasattr(response_context, "request")


def test_AfterResponseMiddleware_toplevel_awaits_async(app: Flask, ndb_stub) -> None:
    from google.appengine.ext import ndb

    middleware_app = cast(WSGIApplication, AfterResponseMiddleware(app))
    tasklet_finished = False

    @ndb.tasklet
    def async_work():
        nonlocal tasklet_finished
        tasklet_finished = True

    def callback():
        async_work()

    @app.route("/async")
    def test_handler_async():
        run_after_response(callback)
        return "OK"

    environ = create_environ(path="/async", base_url="http://localhost")
    run_wsgi_app(middleware_app, environ, buffered=True)

    assert tasklet_finished is True
    assert not hasattr(response_context, "request")


def test_AfterResponseMiddleware_ndb_context_access(app: Flask, ndb_stub) -> None:
    from google.appengine.ext import ndb

    middleware_app = cast(WSGIApplication, AfterResponseMiddleware(app))
    contexts: dict[str, Any] = {}

    class TestModel(ndb.Model):
        val = ndb.StringProperty()

    @app.route("/ndb_test")
    def test_handler():
        contexts["handler"] = ndb.get_context()
        TestModel(id="test_key", val="initial").put()

        @run_after_response
        def callback():
            contexts["callback"] = ndb.get_context()
            entity = TestModel.get_by_id("test_key")
            contexts["read_val"] = entity.val if entity else None
            TestModel(id="test_key2", val="after_response").put()

        return "OK"

    environ = create_environ(path="/ndb_test", base_url="http://localhost")
    run_wsgi_app(middleware_app, environ, buffered=True)

    assert contexts["callback"] is not None
    assert contexts["handler"] is not None
    assert contexts["callback"] is not contexts["handler"]
    assert contexts["read_val"] == "initial"
    saved_entity = TestModel.get_by_id("test_key2")
    assert saved_entity is not None
    assert saved_entity.val == "after_response"


@patch.object(middleware, "_set_secret_key")
def test_install_middleware(mock_set_secret_key: Mock, app: Flask) -> None:
    assert not isinstance(app.wsgi_app, AfterResponseMiddleware)
    install_middleware(app, configure_secret_key=True)
    assert len(app.before_request_funcs) == 0
    mock_set_secret_key.assert_called_once_with(app)
    assert isinstance(app.wsgi_app, AfterResponseMiddleware)


@patch.object(middleware, "_set_secret_key")
def test_install_middleware_with_appspot_redirect(
    mock_set_secret_key: Mock, app: Flask
) -> None:
    assert not isinstance(app.wsgi_app, AppspotRedirectMiddleware)
    install_middleware(app, configure_secret_key=True, include_appspot_redirect=True)
    assert len(app.before_request_funcs) == 0
    mock_set_secret_key.assert_called_once_with(app)
    assert isinstance(app.wsgi_app, AppspotRedirectMiddleware)


def test_set_secret_key_default(app: Flask) -> None:
    assert app.secret_key is None
    _set_secret_key(app)
    assert app.secret_key == Environment.DEFAULT_FLASK_SECRET_KEY


def test_set_secret_key_empty(app: Flask, monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(Environment, "flask_secret_key", lambda: "")

    assert app.secret_key is None
    with pytest.raises(Exception, match="Secret key not set!"):
        _set_secret_key(app)


@patch.object(Environment, "is_prod", return_value=True)
def test_set_secret_key_default_prod(_mock_is_prod: Mock, app: Flask) -> None:
    assert app.secret_key is None
    with pytest.raises(Exception, match="Secret key may not be default in production!"):
        _set_secret_key(app)
