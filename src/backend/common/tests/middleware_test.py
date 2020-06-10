from backend.common.middleware import (
    NdbMiddleware,
    TraceRequestMiddleware,
    install_middleware,
)
from backend.common.profiler import trace_context
import flask
from flask import Flask
from google.cloud.ndb import context as context_module
from werkzeug.wrappers import Request


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
    install_middleware(app)
    assert type(app.wsgi_app) is NdbMiddleware
