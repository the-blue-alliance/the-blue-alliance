from typing import Any, Callable, Optional

from flask import Flask
from google.cloud import ndb
from werkzeug.wrappers import Request
from werkzeug.wsgi import ClosingIterator

from backend.common.environment import Environment
from backend.common.profiler import send_traces, Span, trace_context
from backend.common.redis import RedisClient


class NdbMiddleware(object):

    """
    A middleware that gives each request access to an ndb context
    """

    app: Callable[[Any, Any], Any]
    ndb_client: ndb.Client
    global_cache: Optional[ndb.GlobalCache]

    def __init__(self, app: Callable[[Any, Any], Any]):
        self.app = app
        self.ndb_client = ndb.Client()
        redis_client = RedisClient.get()
        self.global_cache = ndb.RedisCache(redis_client) if redis_client else None

    def __call__(self, environ: Any, start_response: Any):
        with self.ndb_client.context(
            global_cache=self.global_cache,
        ):
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

    # The middlewares get added in order of this last, and each wraps the previous
    # This means, the last one in this list is the "outermost" middleware that runs
    # _first_ for a given request, for the cases when order matters
    middlewares = [
        AfterResponseMiddleware,
        TraceRequestMiddleware,
        NdbMiddleware,
    ]
    for middleware in middlewares:
        app.wsgi_app = middleware(app.wsgi_app)  # type: ignore[override]


def _set_secret_key(app: Flask) -> None:
    from backend.common.sitevars.secrets import Secrets

    secret_key = Secrets.secret_key()
    if Environment.is_prod():
        if not secret_key:
            raise Exception("Secret key not set in production!")
        if secret_key == Secrets.DEFAULT_SECRET_KEY:
            raise Exception("Secret key may not be default in production!")
    app.secret_key = secret_key
