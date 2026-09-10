import json
from unittest.mock import MagicMock

import pytest
from flask import Flask
from werkzeug.exceptions import NotFound

from backend.api.handlers.helpers.model_properties import ModelType
from backend.api.handlers.helpers.model_query_response import (
    combine_json_arrays,
    model_query_response,
    models_query_response,
    multi_models_query_response,
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


def test_combine_json_arrays() -> None:
    assert combine_json_arrays([]) == b"[]"
    assert combine_json_arrays([b"[]", None, b""]) == b"[]"
    assert combine_json_arrays([b"[ ]", b"[]"]) == b"[]"
    assert (
        combine_json_arrays([b'[{"key": "1"}, {"key": "2"}]', b"[]", b'[{"key": "3"}]'])
        == b'[{"key": "1"}, {"key": "2"},{"key": "3"}]'
    )


def test_multi_models_query_response_passthrough(app: Flask) -> None:
    mock_fut1 = MagicMock()
    mock_fut1.get_result.return_value = b'[{"key": "frc254"}]'
    mock_fut2 = MagicMock()
    mock_fut2.get_result.return_value = b"[]"
    mock_fut3 = MagicMock()
    mock_fut3.get_result.return_value = b'[{"key": "frc604"}]'

    mock_q1 = MagicMock()
    mock_q1.fetch_json_async.return_value = mock_fut1
    mock_q2 = MagicMock()
    mock_q2.fetch_json_async.return_value = mock_fut2
    mock_q3 = MagicMock()
    mock_q3.fetch_json_async.return_value = mock_fut3

    with app.app_context():
        resp = multi_models_query_response([mock_q1, mock_q2, mock_q3], model_type=None)

        mock_q1.fetch_json_async.assert_called_once_with(ApiMajorVersion.API_V3)
        mock_q2.fetch_json_async.assert_called_once_with(ApiMajorVersion.API_V3)
        mock_q3.fetch_json_async.assert_called_once_with(ApiMajorVersion.API_V3)
        assert resp.content_type == "application/json"
        assert json.loads(resp.data) == [{"key": "frc254"}, {"key": "frc604"}]


def test_multi_models_query_response_filtered(app: Flask) -> None:
    mock_fut1 = MagicMock()
    mock_fut1.get_result.return_value = [{"key": "frc254", "name": "Team 254"}]
    mock_fut2 = MagicMock()
    mock_fut2.get_result.return_value = [{"key": "frc604", "name": "Team 604"}]

    mock_q1 = MagicMock()
    mock_q1.fetch_dict_async.return_value = mock_fut1
    mock_q2 = MagicMock()
    mock_q2.fetch_dict_async.return_value = mock_fut2

    filter_func = MagicMock(
        side_effect=lambda models, mt: [{"key": m["key"]} for m in models]
    )

    with app.app_context():
        resp = multi_models_query_response(
            [mock_q1, mock_q2],
            model_type=ModelType("simple"),
            filter_func=filter_func,
        )

        mock_q1.fetch_dict_async.assert_called_once_with(ApiMajorVersion.API_V3)
        mock_q2.fetch_dict_async.assert_called_once_with(ApiMajorVersion.API_V3)
        assert json.loads(resp.data) == [{"key": "frc254"}, {"key": "frc604"}]
