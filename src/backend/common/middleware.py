from typing import Any, Callable

from flask import Flask
from google.cloud import ndb
from werkzeug.wrappers import Request
from werkzeug.wsgi import ClosingIterator

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


def install_middleware(app: Flask) -> None:
    app.wsgi_app = NdbMiddleware(TraceRequestMiddleware(AfterResponseMiddleware(app.wsgi_app)))  # type: ignore[override]
