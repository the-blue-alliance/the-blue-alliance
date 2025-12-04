from unittest.mock import patch

import pytest
from flask import Flask, g


from backend.api.handlers.helpers.track_call import track_call_after_response


@pytest.fixture
def app() -> Flask:
    app = Flask(__name__)
    return app


@patch("backend.api.handlers.helpers.track_call.GoogleAnalytics.track_event")
def test_track_call_after_response(mock_track_event, app: Flask) -> None:
    with app.app_context():
        g.auth_owner_id = "owner123"
        g.auth_description = "Test API Key"

        track_call_after_response("teams/list", api_label="2020")

        mock_track_event.assert_called_once_with(
            "owner123",
            "api_v03",
            {
                "client_id": "_owner123",
                "owner_description": "owner123:Test API Key",
                "action": "teams/list",
                "label": "2020",
            },
            run_after=True,
        )


@patch("backend.api.handlers.helpers.track_call.GoogleAnalytics.track_event")
def test_track_call_after_response_with_model_type(
    mock_track_event, app: Flask
) -> None:
    with app.app_context():
        g.auth_owner_id = "owner123"
        g.auth_description = "Test API Key"

        track_call_after_response("teams/list", api_label="2020", model_type="simple")

        mock_track_event.assert_called_once_with(
            "owner123",
            "api_v03",
            {
                "client_id": "_owner123",
                "owner_description": "owner123:Test API Key",
                "action": "teams/list/simple",
                "label": "2020",
            },
            run_after=True,
        )


@patch("backend.api.handlers.helpers.track_call.GoogleAnalytics.track_event")
def test_track_call_after_response_no_label(mock_track_event, app: Flask) -> None:
    with app.app_context():
        g.auth_owner_id = "owner123"
        g.auth_description = "Test API Key"

        track_call_after_response("teams/list")

        mock_track_event.assert_called_once_with(
            "owner123",
            "api_v03",
            {
                "client_id": "_owner123",
                "owner_description": "owner123:Test API Key",
                "action": "teams/list",
                "label": None,
            },
            run_after=True,
        )


@patch("backend.api.handlers.helpers.track_call.GoogleAnalytics.track_event")
def test_track_call_after_response_missing_auth_owner_id(
    mock_track_event, app: Flask
) -> None:
    with app.app_context():
        g.auth_description = "Test API Key"

        track_call_after_response("teams/list")

        mock_track_event.assert_not_called()


@patch("backend.api.handlers.helpers.track_call.GoogleAnalytics.track_event")
def test_track_call_after_response_missing_auth_description(
    mock_track_event, app: Flask
) -> None:
    with app.app_context():
        g.auth_owner_id = "owner123"

        track_call_after_response("teams/list")

        mock_track_event.assert_not_called()


@patch("backend.api.handlers.helpers.track_call.GoogleAnalytics.track_event")
def test_track_call_after_response_non_string_auth_owner_id(
    mock_track_event, app: Flask
) -> None:
    with app.app_context():
        g.auth_owner_id = 12345
        g.auth_description = "Test API Key"

        track_call_after_response("teams/list")

        mock_track_event.assert_not_called()


@patch("backend.api.handlers.helpers.track_call.GoogleAnalytics.track_event")
def test_track_call_after_response_non_string_auth_description(
    mock_track_event, app: Flask
) -> None:
    with app.app_context():
        g.auth_owner_id = "owner123"
        g.auth_description = 12345

        track_call_after_response("teams/list")

        mock_track_event.assert_not_called()
