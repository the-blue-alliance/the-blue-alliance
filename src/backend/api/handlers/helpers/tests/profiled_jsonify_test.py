import json
from unittest.mock import patch

import pytest
from flask import Flask

from backend.api.handlers.helpers.profiled_jsonify import profiled_jsonify


@pytest.fixture
def app() -> Flask:
    app = Flask(__name__)
    return app


def test_profiled_jsonify_dict(app: Flask) -> None:
    with app.app_context():
        data = {"key": "value", "number": 42}
        response = profiled_jsonify(data)

        assert response.content_type == "application/json"
        assert json.loads(response.data) == data


def test_profiled_jsonify_list(app: Flask) -> None:
    with app.app_context():
        data = [1, 2, 3, "test"]
        response = profiled_jsonify(data)

        assert response.content_type == "application/json"
        assert json.loads(response.data) == data


def test_profiled_jsonify_nested(app: Flask) -> None:
    with app.app_context():
        data = {
            "teams": [{"name": "Team 1"}, {"name": "Team 2"}],
            "count": 2,
        }
        response = profiled_jsonify(data)

        assert response.content_type == "application/json"
        assert json.loads(response.data) == data


@patch("backend.api.handlers.helpers.profiled_jsonify.Span")
def test_profiled_jsonify_uses_span(mock_span, app: Flask) -> None:
    with app.app_context():
        profiled_jsonify({"test": "data"})

    mock_span.assert_called_once_with("profiled_jsonify")
