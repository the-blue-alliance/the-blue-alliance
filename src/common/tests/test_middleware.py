from common.middleware import NdbMiddleware, install_middleware
from flask import Flask


def test_NdbMiddleware_init(app: Flask) -> None:
    middleware = NdbMiddleware(app)
    assert middleware.app is app


def test_NdbMiddleware_callable(app: Flask) -> None:
    middleware = NdbMiddleware(app)
    with app.test_request_context("/") as c:
        # TODO: Test that some ndb context is available
        pass


def test_install_middleware(app: Flask) -> None:
    assert not type(app.wsgi_app) is NdbMiddleware
    install_middleware(app)
    assert type(app.wsgi_app) is NdbMiddleware
