import itertools
import time
from typing import Generator
from unittest.mock import patch, ANY

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


def test_GoogleAnalytics_track_event_missing_sitevar() -> None:
    with patch("logging.warning") as mock_warning:
        GoogleAnalytics.track_event("testbed", "test", "test")
        mock_warning.assert_called_with(
            "Missing sitevar: google_analytics.id. Can't track API usage."
        )


@pytest.mark.parametrize(
    "run_after,el,ev", itertools.product([False, True], [None, "test"], [None, 123])
)
def test_GoogleAnalytics_track_event(run_after, el, ev) -> None:
    from backend.common.sitevars.google_analytics_id import GoogleAnalyticsID

    sitevar = GoogleAnalyticsID._fetch_sitevar()
    sitevar.contents["GOOGLE_ANALYTICS_ID"] = "abc"

    # Ensure response_context has a request object so run_after callbacks can be queued
    response_context.request = Request(create_environ(path="/"))

    with patch("requests.post") as mock_post, patch("time.time", return_value=12345.0):
        GoogleAnalytics.track_event(
            "testbed",
            "test_category",
            "test_action",
            event_label=el,
            event_value=ev,
            run_after=run_after,
        )
        if run_after:
            mock_post.assert_not_called()
        execute_callbacks()

    mock_post.assert_called()
    args, kwargs = mock_post.call_args

    assert len(args) == 1
    assert len(kwargs) == 2  # json and timeout
    assert args[0] == "https://www.google-analytics.com/mp/collect?measurement_id=abc&api_secret=REPLACE_WITH_API_SECRET"
    assert kwargs["timeout"] == 10

    event_params = {
        "event_category": "test_category",
        "event_action": "test_action",
        "client_id_raw": "testbed",  # This should match the first parameter to track_event
    }
    if el:
        event_params["event_label"] = el
    if ev:
        event_params["event_value"] = ev

    expected_payload = {
        "client_id": "6dcf939a-da96-33c4-acd1-51208db9ceaa",
        "events": [{
            "name": "test_category_test_action",
            "params": event_params,
            "timestamp_micros": 12345000000
        }],
        "non_personalized_ads": True
    }

    assert kwargs["json"] == expected_payload
