import json
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask
from werkzeug.test import create_environ
from werkzeug.wrappers import Request

from backend.common.google_analytics import GoogleAnalytics
from backend.common.run_after_response import execute_callbacks, response_context


@pytest.fixture(autouse=True)
def auto_add_ndb_stub(ndb_stub) -> None:
    pass


@pytest.fixture(autouse=True)
def run_with_werkzeug_context(app: Flask) -> Generator:
    with app.test_request_context("/"):
        yield


def test_GoogleAnalytics_track_event_missing_google_analytics_id() -> None:
    with patch("logging.warning") as mock_warning:
        GoogleAnalytics.track_event("testbed", "test", {"test_param": "test_value"})
        mock_warning.assert_called_with(
            "Missing sitevar: google_analytics.id GOOGLE_ANALYTICS_ID. Can't track API usage."
        )


def test_GoogleAnalytics_track_event_missing_api_secret() -> None:
    from backend.common.sitevars.google_analytics_id import GoogleAnalyticsID

    sitevar = GoogleAnalyticsID._fetch_sitevar()
    sitevar.contents["GOOGLE_ANALYTICS_ID"] = "abc"
    sitevar.contents["API_SECRET"] = ""

    with patch("logging.warning") as mock_warning:
        GoogleAnalytics.track_event("testbed", "test", {"test_param": "test_value"})
        mock_warning.assert_called_with(
            "Missing sitevar: google_analytics.id API_SECRET. Can't track API usage."
        )


@pytest.mark.parametrize("run_after", [False, True])
def test_GoogleAnalytics_track_event(run_after) -> None:
    from backend.common.sitevars.google_analytics_id import GoogleAnalyticsID

    sitevar = GoogleAnalyticsID._fetch_sitevar()
    sitevar.contents["GOOGLE_ANALYTICS_ID"] = "G-ABC123DEF4"
    sitevar.contents["API_SECRET"] = "test_secret"

    # Ensure response_context has a request object so run_after callbacks can be queued
    response_context.request = Request(create_environ(path="/"))

    mock_future = MagicMock()
    mock_context = MagicMock()
    mock_context.urlfetch.return_value = mock_future

    with patch("google.appengine.ext.ndb.get_context", return_value=mock_context):
        GoogleAnalytics.track_event(
            "testbed",
            "test_event",
            {"test_param": "test_value", "another_param": 123},
            run_after=run_after,
        )
        if run_after:
            mock_context.urlfetch.assert_not_called()
        execute_callbacks()

    mock_context.urlfetch.assert_called_once()
    mock_future.get_result.assert_called_once()
    args, kwargs = mock_context.urlfetch.call_args

    assert len(args) == 1
    assert len(kwargs) == 4
    assert (
        args[0]
        == "https://www.google-analytics.com/mp/collect?measurement_id=G-ABC123DEF4&api_secret=test_secret"
    )
    assert kwargs["deadline"] == 10
    assert kwargs["method"] == "POST"
    assert kwargs["headers"] == {"Content-Type": "application/json"}

    # Check the payload structure for GA4
    payload_bytes = kwargs["payload"]
    payload = json.loads(payload_bytes.decode("utf-8"))

    assert "client_id" in payload
    assert "events" in payload
    assert len(payload["events"]) == 1

    event = payload["events"][0]
    assert event["name"] == "test_event"
    assert event["params"] == {"test_param": "test_value", "another_param": 123}

    # Verify client_id is a UUID (should be deterministic based on the input)
    import uuid

    expected_client_id = str(uuid.uuid3(uuid.NAMESPACE_X500, "testbed"))
    assert payload["client_id"] == expected_client_id


def test_GoogleAnalytics_track_event_urlfetch_failure() -> None:
    from backend.common.sitevars.google_analytics_id import GoogleAnalyticsID

    sitevar = GoogleAnalyticsID._fetch_sitevar()
    sitevar.contents["GOOGLE_ANALYTICS_ID"] = "G-ABC123DEF4"
    sitevar.contents["API_SECRET"] = "test_secret"

    mock_future = MagicMock()
    mock_future.get_result.side_effect = Exception("urlfetch deadline exceeded")
    mock_context = MagicMock()
    mock_context.urlfetch.return_value = mock_future

    with patch("google.appengine.ext.ndb.get_context", return_value=mock_context):
        with patch("logging.warning") as mock_warning:
            # Should not raise
            GoogleAnalytics.track_event(
                "testbed",
                "test_event",
                {"test_param": "test_value"},
            )
            mock_warning.assert_called_once()
            assert "Failed to send GA4 event" in mock_warning.call_args[0][0]
