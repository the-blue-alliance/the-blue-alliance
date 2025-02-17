import base64
import io

from flask import Flask, request, Response
from google.appengine.ext import deferred

from backend.common.url_converters import (
    has_regex_url_converter,
    install_regex_url_converter,
)


def _decode_deferred_payload(environ):
    try:
        request_body_size = int(environ.get("CONTENT_LENGTH", 0))
    except ValueError:
        request_body_size = 0

    request_body = environ["wsgi.input"].read(request_body_size)

    decoded_body = base64.b64decode(request_body)
    environ["CONTENT_LENGTH"] = len(decoded_body)
    environ["wsgi.input"] = io.BytesIO(decoded_body)
    return environ


def handle_defer(path: str) -> Response:
    updated_environ = _decode_deferred_payload(request.environ)
    return deferred.application.post(updated_environ)


def install_defer_routes(app: Flask) -> None:
    # Requires regex URL converter
    if not has_regex_url_converter(app):
        install_regex_url_converter(app)

    app.add_url_rule(
        '/_ah/queue/<regex("deferred.*?"):path>',
        view_func=handle_defer,
        methods=["POST"],
    )
