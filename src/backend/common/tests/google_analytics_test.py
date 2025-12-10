from typing import Generator
from unittest.mock import patch

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

    with patch("requests.post") as mock_post:
        GoogleAnalytics.track_event(
            "testbed",
            "test_event",
            {"test_param": "test_value", "another_param": 123},
            run_after=run_after,
        )
        if run_after:
            mock_post.assert_not_called()
        execute_callbacks()

    mock_post.assert_called()
    args, kwargs = mock_post.call_args

    assert len(args) == 1
    assert len(kwargs) == 2
    assert (
        args[0]
        == "https://www.google-analytics.com/mp/collect?measurement_id=G-ABC123DEF4&api_secret=test_secret"
    )
    assert kwargs["timeout"] == 10

    # Check the payload structure for GA4
    payload = kwargs["json"]
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
