from flask import Flask
from typing import Any, Callable


class NdbMiddleware(object):

    """
    A middleware that gives each request access to an ndb context
    """

    app: Callable[[Any, Any], Any]

    def __init__(self, app: Callable[[Any, Any], Any]):
        self.app = app

    def __call__(self, environ: Any, start_response: Any):
        return self.app(environ, start_response)


def install_middleware(app: Flask) -> None:
    app.wsgi_app = NdbMiddleware(app.wsgi_app)  # type: ignore[override]
