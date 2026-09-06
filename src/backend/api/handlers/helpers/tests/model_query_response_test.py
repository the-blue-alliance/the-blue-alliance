import json
from unittest.mock import MagicMock

import pytest
from flask import Flask
from werkzeug.exceptions import NotFound

from backend.api.handlers.helpers.model_properties import ModelType
from backend.api.handlers.helpers.model_query_response import (
    model_query_response,
    models_query_response,
)
from backend.common.consts.api_version import ApiMajorVersion


@pytest.fixture
def app() -> Flask:
    app = Flask(__name__)
    return app


def test_model_query_response_passthrough(app: Flask) -> None:
    mock_query = MagicMock()
    mock_query.fetch_json.return_value = b'{"key": "2024casf", "name": "Event"}'

    with app.app_context():
        resp = model_query_response(mock_query, model_type=None)

        mock_query.fetch_json.assert_called_once_with(ApiMajorVersion.API_V3)
        mock_query.fetch_dict.assert_not_called()
        assert resp.content_type == "application/json"
        assert json.loads(resp.data) == {"key": "2024casf", "name": "Event"}


def test_model_query_response_404(app: Flask) -> None:
    mock_query = MagicMock()
    mock_query.fetch_json.return_value = None

    with app.app_context():
        with pytest.raises(NotFound):
            model_query_response(mock_query, model_type=None)


def test_model_query_response_filtered(app: Flask) -> None:
    mock_query = MagicMock()
    mock_query.fetch_dict.return_value = {
        "key": "2024casf",
        "name": "Event",
        "secret": "hidden",
    }
    filter_func = MagicMock(
        side_effect=lambda models, mt: [{"key": m["key"]} for m in models]
    )

    with app.app_context():
        resp = model_query_response(
            mock_query,
            model_type=ModelType("simple"),
            filter_func=filter_func,
        )

        mock_query.fetch_dict.assert_called_once_with(ApiMajorVersion.API_V3)
        mock_query.fetch_json.assert_not_called()
        assert json.loads(resp.data) == {"key": "2024casf"}


def test_models_query_response_passthrough(app: Flask) -> None:
    mock_query = MagicMock()
    mock_query.fetch_json.return_value = b'[{"key": "2024casf"}]'

    with app.app_context():
        resp = models_query_response(mock_query, model_type=None)

        mock_query.fetch_json.assert_called_once_with(ApiMajorVersion.API_V3)
        mock_query.fetch_dict.assert_not_called()
        assert json.loads(resp.data) == [{"key": "2024casf"}]


def test_models_query_response_filtered(app: Flask) -> None:
    mock_query = MagicMock()
    mock_query.fetch_dict.return_value = [
        {"key": "2024casf", "name": "Event"},
        {"key": "2024sj", "name": "Event 2"},
    ]
    filter_func = MagicMock(
        side_effect=lambda models, mt: [{"key": m["key"]} for m in models]
    )

    with app.app_context():
        resp = models_query_response(
            mock_query,
            model_type=ModelType("simple"),
            filter_func=filter_func,
        )

        mock_query.fetch_dict.assert_called_once_with(ApiMajorVersion.API_V3)
        mock_query.fetch_json.assert_not_called()
        assert json.loads(resp.data) == [{"key": "2024casf"}, {"key": "2024sj"}]
