from typing import cast
from unittest.mock import Mock, patch
from wsgiref.types import WSGIApplication

import pytest
from _pytest.monkeypatch import MonkeyPatch
from flask import Flask
from werkzeug.test import create_environ, run_wsgi_app
from werkzeug.wrappers import Request

from backend.common import middleware
from backend.common.environment import Environment
from backend.common.middleware import (
    _set_secret_key,
    AfterResponseMiddleware,
    AppspotRedirectMiddleware,
    install_middleware,
    TraceRequestMiddleware,
)
from backend.common.profiler import trace_context
from backend.common.run_after_response import run_after_response


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
