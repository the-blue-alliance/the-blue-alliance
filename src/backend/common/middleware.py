from typing import Any, Callable

from flask import Flask
from google.cloud import ndb
from werkzeug.wrappers import Request
from werkzeug.wsgi import ClosingIterator

from backend.common.environment import Environment
from backend.common.profiler import send_traces, Span, trace_context


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


class TraceRequestMiddleware(object):
    """
    A middleware that gives trace_context access to the request
    """

    app: Callable[[Any, Any], Any]

    def __init__(self, app: Callable[[Any, Any], Any]):
        self.app = app

    def __call__(self, environ: Any, start_response: Any):
        trace_context.request = Request(environ)  # pyre-ignore[16]
        return self.app(environ, start_response)


class AfterResponseMiddleware:
    """
    A middleware that handles tasks after handling the response
    """

    app: Callable[[Any, Any], Any]

    def __init__(self, app: Callable[[Any, Any], Any]):
        self.app = app

    def __call__(self, environ: Any, start_response: Any):
        return ClosingIterator(self.app(environ, start_response), self._run)

    def _run(self):
        with Span("Running AfterResponseMiddleware"):
            pass
        send_traces()


def install_middleware(app: Flask, configure_secret_key: bool = True) -> None:
    @app.before_first_request
    def _app_before():
        if configure_secret_key:
            _set_secret_key(app)

    app.wsgi_app = NdbMiddleware(TraceRequestMiddleware(AfterResponseMiddleware(app.wsgi_app)))  # type: ignore[override]


def _set_secret_key(app: Flask) -> None:
    from backend.common.sitevars.secrets import Secrets

    secret_key = Secrets.secret_key()
    if Environment.is_prod():
        if not secret_key:
            raise Exception("Secret key not set in production!")
        if secret_key == Secrets.DEFAULT_SECRET_KEY:
            raise Exception("Secret key may not be default in production!")
    app.secret_key = Secrets.secret_key()
