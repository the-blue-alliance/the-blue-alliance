from unittest.mock import Mock, patch

import flask
import pytest
from _pytest.monkeypatch import MonkeyPatch
from flask import Flask
from werkzeug.test import run_wsgi_app
from werkzeug.wrappers import Request

import backend
from backend.common.environment import Environment
from backend.common.middleware import (
    _set_secret_key,
    AfterResponseMiddleware,
    install_middleware,
    TraceRequestMiddleware,
)
from backend.common.profiler import trace_context
from backend.common.run_after_response import run_after_response


def test_TraceRequestMiddleware_init(app: Flask) -> None:
    middleware = TraceRequestMiddleware(app)
    assert middleware.app is app


def test_TraceRequestMiddleware_callable(app: Flask) -> None:
    middleware = TraceRequestMiddleware(app)

    def start_response(status, headers):
        pass

    with app.test_request_context("/"):
        middleware(flask.request.environ, start_response)

    assert isinstance(trace_context.request, Request)


def test_AfterResponseMiddleware_init(app: Flask) -> None:
    middleware = AfterResponseMiddleware(app)
    assert middleware.app is app


def test_AfterResponseMiddleware_callable(app: Flask) -> None:
    middleware = AfterResponseMiddleware(app)
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
    with app.test_request_context("/0"):
        run_wsgi_app(middleware, flask.request.environ, buffered=True)
    callback1.assert_not_called()
    callback2.assert_not_called()

    # Test first callback.
    callback1.assert_not_called()
    callback2.assert_not_called()
    with app.test_request_context("/1"):
        run_wsgi_app(middleware, flask.request.environ, buffered=True)
    callback1.assert_called_once()
    callback2.assert_not_called()

    # Ensure a second call doesn't call the first callback again.
    callback1.assert_called_once()
    callback2.assert_not_called()
    with app.test_request_context("/2"):
        run_wsgi_app(middleware, flask.request.environ, buffered=True)
    callback1.assert_called_once()
    callback2.assert_called_once()


def test_install_middleware(app: Flask) -> None:
    assert not type(app.wsgi_app) is TraceRequestMiddleware
    with patch.object(
        backend.common.middleware, "_set_secret_key"
    ) as mock_set_secret_key:
        install_middleware(app, configure_secret_key=True)
        assert len(app.before_request_funcs) == 0
    mock_set_secret_key.assert_called_once_with(app)
    assert type(app.wsgi_app) is TraceRequestMiddleware


def test_set_secret_key_default(app: Flask) -> None:
    assert app.secret_key is None
    _set_secret_key(app)
    assert app.secret_key == Environment.DEFAULT_FLASK_SECRET_KEY


def test_set_secret_key_empty(app: Flask, monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(Environment, "flask_secret_key", lambda: "")

    assert app.secret_key is None
    with pytest.raises(Exception, match="Secret key not set!"):
        _set_secret_key(app)


def test_set_secret_key_default_prod(app: Flask) -> None:
    assert app.secret_key is None
    with patch.object(Environment, "is_prod", return_value=True):
        with pytest.raises(
            Exception, match="Secret key may not be default in production!"
        ):
            _set_secret_key(app)
