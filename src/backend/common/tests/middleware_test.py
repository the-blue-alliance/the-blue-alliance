import json
from unittest.mock import patch

import flask
import pytest
from flask import Flask
from google.cloud.ndb import context as context_module
from werkzeug.wrappers import Request

import backend
from backend.common.environment import Environment
from backend.common.middleware import (
    _set_secret_key,
    install_middleware,
    NdbMiddleware,
    TraceRequestMiddleware,
)
from backend.common.models.sitevar import Sitevar
from backend.common.profiler import trace_context


def test_NdbMiddleware_init(app: Flask) -> None:
    middleware = NdbMiddleware(app)
    assert middleware.app is app


def test_NdbMiddleware_callable(app: Flask) -> None:
    middleware = NdbMiddleware(app)

    def start_response(status, headers):
        context = context_module.get_context()
        assert context.client is middleware.ndb_client

    with app.test_request_context("/"):
        middleware(flask.request.environ, start_response)


def test_TraceRequestMiddleware_init(app: Flask) -> None:
    middleware = TraceRequestMiddleware(app)
    assert middleware.app is app


def test_TraceRequestMiddleware_callable(app: Flask) -> None:
    middleware = TraceRequestMiddleware(app)

    def start_response(status, headers):
        pass

    with app.test_request_context("/"):
        middleware(flask.request.environ, start_response)

    assert type(trace_context.request) == Request


def test_install_middleware(app: Flask) -> None:
    assert not type(app.wsgi_app) is NdbMiddleware
    with patch.object(
        backend.common.middleware, "_set_secret_key"
    ) as mock_set_secret_key:
        install_middleware(app)
        assert len(app.before_first_request_funcs) > 0
        app.try_trigger_before_first_request_functions()
    mock_set_secret_key.assert_called_with(app)
    assert type(app.wsgi_app) is NdbMiddleware


def test_set_secret_key_default(ndb_context, app: Flask) -> None:
    assert app.secret_key is None
    _set_secret_key(app)
    assert app.secret_key == "thebluealliance"


def test_set_secret_key_not_default(ndb_context, app: Flask) -> None:
    secret_key = "some_new_secret_key"
    Sitevar.get_or_insert(
        "secrets", values_json=json.dumps({"secret_key": secret_key})
    )

    assert app.secret_key is None
    _set_secret_key(app)
    assert app.secret_key == secret_key


def test_set_secret_key_empty_prod(ndb_context, app: Flask) -> None:
    Sitevar.get_or_insert("secrets", values_json=json.dumps({"secret_key": ""}))

    assert app.secret_key is None
    with patch.object(Environment, "is_prod", return_value=True):
        with pytest.raises(Exception, match="Secret key not set in production!"):
            _set_secret_key(app)


def test_set_secret_key_default_prod(ndb_context, app: Flask) -> None:
    assert app.secret_key is None
    with patch.object(Environment, "is_prod", return_value=True):
        with pytest.raises(
            Exception, match="Secret key may not be default in production!"
        ):
            _set_secret_key(app)


def test_set_secret_key_prod(ndb_context, app: Flask) -> None:
    secret_key = "some_new_secret_key"
    Sitevar.get_or_insert(
        "secrets", values_json=json.dumps({"secret_key": secret_key})
    )

    assert app.secret_key is None
    with patch.object(Environment, "is_prod", return_value=True):
        _set_secret_key(app)
    assert app.secret_key == secret_key
