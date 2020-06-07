from backend.common.middleware import NdbMiddleware, install_middleware
import flask
from flask import Flask
from google.cloud.ndb import context as context_module


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


def test_install_middleware(app: Flask) -> None:
    assert not type(app.wsgi_app) is NdbMiddleware
    install_middleware(app)
    assert type(app.wsgi_app) is NdbMiddleware
