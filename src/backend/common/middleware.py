from flask import Flask
from google.cloud import ndb
from typing import Any, Callable


class NdbMiddleware(object):

    """
    A middleware that gives each request access to an ndb context
    """

    app: Callable[[Any, Any], Any]
    ndb_client: ndb.Client

    def __init__(self, app: Callable[[Any, Any], Any]):
        self.app = app
        self.ndb_client = ndb.Client()

    def __call__(self, environ: Any, start_response: Any):
        with self.ndb_client.context():
            return self.app(environ, start_response)


def install_middleware(app: Flask) -> None:
    app.wsgi_app = NdbMiddleware(app.wsgi_app)  # type: ignore[override]
