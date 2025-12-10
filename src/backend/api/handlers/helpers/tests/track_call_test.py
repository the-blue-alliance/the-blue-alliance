from unittest.mock import patch

import pytest
from flask import Flask, g


from backend.api.handlers.helpers import track_call
from backend.api.handlers.helpers.track_call import track_call_after_response


@pytest.fixture
def app() -> Flask:
    app = Flask(__name__)
    return app


@patch("backend.api.handlers.helpers.track_call.defer_safe_async")
def test_track_call_after_response(mock_defer_safe_async, app: Flask) -> None:
    with app.app_context():
        g.auth_owner_id = "owner123"
        g.auth_description = "Test API Key"

        track_call_after_response("teams/list", api_label="2020")

        mock_defer_safe_async.assert_called_once_with(
            track_call.GoogleAnalytics.track_event,
            "owner123",
            "api_v03",
            {
                "client_id": "_owner123",
                "owner_description": "owner123:Test API Key",
                "action": "teams/list",
                "label": "2020",
            },
            _queue="api-track-call",
            _url="/_ah/queue/deferred_track_call_apiv3",
        )


@patch("backend.api.handlers.helpers.track_call.defer_safe_async")
def test_track_call_after_response_with_model_type(mock_defer_safe_async, app: Flask) -> None:
    with app.app_context():
        g.auth_owner_id = "owner123"
        g.auth_description = "Test API Key"

        track_call_after_response("teams/list", api_label="2020", model_type="simple")

        mock_defer_safe_async.assert_called_once_with(
            track_call.GoogleAnalytics.track_event,
            "owner123",
            "api_v03",
            {
                "client_id": "_owner123",
                "owner_description": "owner123:Test API Key",
                "action": "teams/list/simple",
                "label": "2020",
            },
            _queue="api-track-call",
            _url="/_ah/queue/deferred_track_call_apiv3",
        )


@patch("backend.api.handlers.helpers.track_call.defer_safe_async")
def test_track_call_after_response_no_label(mock_defer_safe_async, app: Flask) -> None:
    with app.app_context():
        g.auth_owner_id = "owner123"
        g.auth_description = "Test API Key"

        track_call_after_response("teams/list")

        mock_defer_safe_async.assert_called_once_with(
            track_call.GoogleAnalytics.track_event,
            "owner123",
            "api_v03",
            {
                "client_id": "_owner123",
                "owner_description": "owner123:Test API Key",
                "action": "teams/list",
                "label": None,
            },
            _queue="api-track-call",
            _url="/_ah/queue/deferred_track_call_apiv3",
        )


@patch("backend.api.handlers.helpers.track_call.defer_safe_async")
def test_track_call_after_response_missing_auth_owner_id(
    mock_defer_safe_async, app: Flask
) -> None:
    with app.app_context():
        g.auth_description = "Test API Key"

        track_call_after_response("teams/list")

        mock_defer_safe_async.assert_not_called()


@patch("backend.api.handlers.helpers.track_call.defer_safe_async")
def test_track_call_after_response_missing_auth_description(
    mock_defer_safe_async, app: Flask
) -> None:
    with app.app_context():
        g.auth_owner_id = "owner123"

        track_call_after_response("teams/list")

        mock_defer_safe_async.assert_not_called()


@patch("backend.api.handlers.helpers.track_call.defer_safe_async")
def test_track_call_after_response_non_string_auth_owner_id(
    mock_defer_safe_async, app: Flask
) -> None:
    with app.app_context():
        g.auth_owner_id = 12345
        g.auth_description = "Test API Key"

        track_call_after_response("teams/list")

        mock_defer_safe_async.assert_not_called()


@patch("backend.api.handlers.helpers.track_call.defer_safe_async")
def test_track_call_after_response_non_string_auth_description(
    mock_defer_safe_async, app: Flask
) -> None:
    with app.app_context():
        g.auth_owner_id = "owner123"
        g.auth_description = 12345

        track_call_after_response("teams/list")

        mock_defer_safe_async.assert_not_called()
