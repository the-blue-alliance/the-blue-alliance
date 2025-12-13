import base64
from unittest.mock import patch

from flask import Flask

from backend.common.deferred.defer_handler import handle_defer, install_defer_routes
from backend.common.url_converters import install_regex_url_converter


def test_install_defer_routes():
    route = '/_ah/queue/<regex("deferred.*?"):path>'
    app = Flask(__name__)
    rules = [r for r in app.url_map.iter_rules() if str(r) == route]
    assert len(rules) == 0
    install_defer_routes(app)
    rules = [r for r in app.url_map.iter_rules() if str(r) == route]
    assert len(rules) == 1
    rule = rules[0]
    assert rule.methods == {"OPTIONS", "POST"}
    assert rule.endpoint == "handle_defer"


def test_install_defer_routes_regex():
    app = Flask(__name__)

    with patch(
        "backend.common.deferred.defer_handler.install_regex_url_converter",
        wraps=install_regex_url_converter,
    ) as mock_install_regex_url_converter:
        install_defer_routes(app)

    mock_install_regex_url_converter.assert_called()


def test_install_defer_routes_regex_already_installed():
    app = Flask(__name__)

    install_regex_url_converter(app)

    with patch(
        "backend.common.deferred.defer_handler.has_regex_url_converter",
        return_value=True,
    ), patch(
        "backend.common.deferred.defer_handler.install_regex_url_converter",
        wraps=install_regex_url_converter,
    ) as mock_install_regex_url_converter:
        install_defer_routes(app)

    mock_install_regex_url_converter.assert_not_called()


def test_handle_defer():
    app = Flask(__name__)
    with app.test_request_context() as request_context, patch(
        "google.appengine.ext.deferred.application.post"
    ) as mock_post:
        environ = request_context.request.environ
        handle_defer("/some/path")

    mock_post.assert_called_with(environ)


def test_handle_defer_decodes_body():
    app = Flask(__name__)
    body = base64.b64encode(b"foo")
    with app.test_request_context(data=body) as request_context, patch(
        "google.appengine.ext.deferred.application.post"
    ) as mock_post:
        request_context.request.environ
        environ = request_context.request.environ

        handle_defer("/some/path")

    mock_post.assert_called_with(environ)
    mock_calls = mock_post.call_args_list
    assert len(mock_calls) == 1
    assert mock_calls[0].args[0]["wsgi.input"].read() == b"foo"
