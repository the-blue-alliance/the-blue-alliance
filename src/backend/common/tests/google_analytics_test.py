import itertools
from typing import Generator
from unittest.mock import patch

import pytest
from flask import Flask
from google.appengine.ext import ndb
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

    with patch("requests.get") as mock_get:
        GoogleAnalytics.track_event(
            "testbed",
            "test",
            "test",
            event_label=el,
            event_value=ev,
            run_after=run_after,
        )
        if run_after:
            mock_get.assert_not_called()
        execute_callbacks()

    mock_get.assert_called()
    args, kwargs = mock_get.call_args

    assert len(args) == 1
    assert len(kwargs) == 2
    assert args[0] == "https://www.google-analytics.com/collect"
    assert kwargs["timeout"] == 10

    query_components_expected = {
        "v": 1,
        "tid": "abc",
        "cid": "6dcf939a-da96-33c4-acd1-51208db9ceaa",
        "t": "event",
        "ec": "test",
        "ea": "test",
        "cd1": "testbed",
        "ni": 1,
        "sc": "end",
    }
    if el:
        query_components_expected["el"] = el
    if ev:
        query_components_expected["ev"] = ev

    assert kwargs["params"] == query_components_expected
