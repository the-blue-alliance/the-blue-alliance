from flask import Flask, request, Response
from google.appengine.ext import deferred

from backend.common.url_converters import (
    has_regex_url_converter,
    install_regex_url_converter,
)


def handle_defer(path: str) -> Response:
    return deferred.application.post(request.environ)


def install_defer_routes(app: Flask) -> None:
    # Requires regex URL converter
    if not has_regex_url_converter(app):
        install_regex_url_converter(app)

    app.add_url_rule(
        '/_ah/queue/<regex("deferred.*?"):path>',
        view_func=handle_defer,
        methods=["POST"],
    )
