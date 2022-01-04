from typing import Any, Callable

from flask import Flask
from werkzeug.wrappers import Request
from werkzeug.wsgi import ClosingIterator

from backend.common.environment import Environment
from backend.common.profiler import send_traces, Span, trace_context
from backend.common.run_after_response import execute_callbacks, local_context


class TraceRequestMiddleware:
    """
    A middleware that gives trace_context access to the request
    """

    app: Callable[[Any, Any], Any]

    def __init__(self, app: Callable[[Any, Any], Any]):
        self.app = app

    def __call__(self, environ: Any, start_response: Any):
        trace_context.request = Request(environ)
        return self.app(environ, start_response)


class AfterResponseMiddleware:
    """
    A middleware that handles tasks after handling the response.
    """

    app: Callable[[Any, Any], Any]

    def __init__(self, app: Callable[[Any, Any], Any]):
        self.app = app

    def __call__(self, environ: Any, start_response: Any):
        local_context.request = Request(environ)
        return ClosingIterator(self.app(environ, start_response), self._run_after)

    def _run_after(self):
        with Span("Running AfterResponseMiddleware"):
            pass
        send_traces()
        execute_callbacks()


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
    ]
    for middleware in middlewares:
        app.wsgi_app = middleware(app.wsgi_app)  # type: ignore[override]


def _set_secret_key(app: Flask) -> None:
    from backend.common.sitevars.flask_secrets import FlaskSecrets

    secret_key = FlaskSecrets.secret_key()
    if Environment.is_prod():
        if not secret_key:
            raise Exception("Secret key not set in production!")
        if secret_key == FlaskSecrets.DEFAULT_SECRET_KEY:
            raise Exception("Secret key may not be default in production!")
    app.secret_key = secret_key
