import logging
from typing import Any, Callable, Optional

from flask import abort, Flask, request
from google.auth.transport import requests
from google.cloud import ndb
from google.oauth2 import id_token
from werkzeug.wrappers import Request
from werkzeug.wsgi import ClosingIterator

from backend.common.environment import Environment
from backend.common.profiler import send_traces, Span, trace_context
from backend.common.redis import RedisClient
from backend.common.run_after_response import execute_callbacks


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


class AfterResponseMiddleware(NdbMiddleware):
    """
    A middleware that handles tasks after handling the response.
    Inherits from NdbMiddleware to access the ndb context.
    """

    def __call__(self, environ: Any, start_response: Any):
        return ClosingIterator(self.app(environ, start_response), self._run_after)

    def _run_after(self):
        with Span("Running AfterResponseMiddleware"):
            pass
        send_traces()
        with self.ndb_client.context(global_cache=self.global_cache):
            execute_callbacks()


def install_backend_security(app: Flask) -> None:
    @app.before_request
    def _confirm_security_headers():
        # Only allow signed requests from TBA services, cron job, or task queue
        task_header = request.headers.get("X-AppEngine-TaskName")
        task_header_dev = request.headers.get("X-Google-TBA-RedisTask")
        cron_header = request.headers.get("X-Appengine-Cron")
        auth_header = request.headers.get("Authorization")
        if task_header or task_header_dev or cron_header:
            return
        elif auth_header:
            # Verify that a request is coming from another TBA service
            # https://cloud.google.com/appengine/docs/standard/python/migrate-to-python3/migrate-app-identity

            # The auth_header must be in the form Authorization: Bearer token.
            bearer, token = auth_header.split()
            if bearer.lower() != 'bearer':
                return abort(403)

            try:
                info = id_token.verify_oauth2_token(token, requests.Request())
                service_account_email = info['email']
                incoming_app_id, domain = service_account_email.split('@')
                if domain != 'appspot.gserviceaccount.com':  # Not App Engine svc acct
                    return abort(403)

                project = Environment.project()
                if not project:
                    return abort(403)

                if incoming_app_id != project:
                    return abort(403)

                # TODO: Need to verify things here...
                print(f"Info: {info}")

                return
            except Exception as e:
                logging.warning('Request has bad OAuth2 id token: {}'.format(e))
                return abort(403)

        return abort(401)


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
    from backend.common.sitevars.flask_secrets import FlaskSecrets

    secret_key = FlaskSecrets.secret_key()
    if Environment.is_prod():
        if not secret_key:
            raise Exception("Secret key not set in production!")
        if secret_key == FlaskSecrets.DEFAULT_SECRET_KEY:
            raise Exception("Secret key may not be default in production!")
    app.secret_key = secret_key
