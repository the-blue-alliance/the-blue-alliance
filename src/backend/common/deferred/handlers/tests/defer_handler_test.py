import pickle
from unittest.mock import patch

import pytest
import werkzeug
from flask import Flask, Response

from backend.common.deferred.handlers.defer_handler import (
    handle_defer,
    install_defer_routes,
    PermanentTaskFailure,
    run,
)
from backend.common.deferred.tasks.task import Task
from backend.common.environment import Environment
from backend.common.url_converters import install_regex_url_converter


def test_install_defer_routes():
    route = '/_ah/queue/<regex("deferred.*"):path>'
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
        "backend.common.deferred.handlers.defer_handler.install_regex_url_converter",
        wraps=install_regex_url_converter,
    ) as mock_install_regex_url_converter:
        install_defer_routes(app)

    mock_install_regex_url_converter.assert_called()


def test_install_defer_routes_regex_already_installed():
    app = Flask(__name__)

    install_regex_url_converter(app)

    with patch(
        "backend.common.deferred.handlers.defer_handler.has_regex_url_converter",
        return_value=True,
    ), patch(
        "backend.common.deferred.handlers.defer_handler.install_regex_url_converter",
        wraps=install_regex_url_converter,
    ) as mock_install_regex_url_converter:
        install_defer_routes(app)

    mock_install_regex_url_converter.assert_not_called()


def test_handle_defer():
    task = Task(method, "a", b="c")
    data = task.serialize()

    app = Flask(__name__)
    with app.test_request_context(data=data), patch(
        "backend.common.deferred.handlers.defer_handler.run"
    ) as mock_run, pytest.raises(werkzeug.exceptions.Forbidden):
        handle_defer("/some/path")

    mock_run.assert_not_called()


def test_handle_defer_task_name_header():
    task = Task(method, "a", b="c")
    data = task.serialize()

    app = Flask(__name__)
    with app.test_request_context(
        headers={"X-AppEngine-TaskName": 123}, data=data
    ), patch("backend.common.deferred.handlers.defer_handler.run") as mock_run:
        response = handle_defer("/some/path")

    assert type(response) is Response
    assert response.status_code == 200
    assert mock_run.called_with(data)


def test_handle_defer_dev_env():
    task = Task(method, "a", b="c")
    data = task.serialize()

    app = Flask(__name__)
    with app.test_request_context(data=data), patch(
        "backend.common.deferred.handlers.defer_handler.run"
    ) as mock_run, patch.object(Environment, "is_dev", return_value=True):
        response = handle_defer("/some/path")

    assert type(response) is Response
    assert response.status_code == 200
    assert mock_run.called_with(data)


def test_run():
    task = Task(method, "a", b="c")
    data = task.serialize()

    with patch(
        "backend.common.deferred.handlers.tests.defer_handler_test.method"
    ) as mock_method:
        run(data)

    mock_method.assert_called_with("a", b="c")


def test_run_raise():
    task = Task(method, "a", b="c")
    data = task.serialize()

    with patch.object(pickle, "loads", side_effect=Exception()), patch(
        "backend.common.deferred.handlers.tests.defer_handler_test.method"
    ) as mock_method, pytest.raises(PermanentTaskFailure):
        run(data)

    mock_method.assert_not_called()


def method(a, *, b):
    pass
