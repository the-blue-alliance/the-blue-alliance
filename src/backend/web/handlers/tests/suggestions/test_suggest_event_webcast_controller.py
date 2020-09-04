from datetime import datetime
from typing import cast, List
from unittest.mock import Mock, patch
from urllib.parse import urlparse

import pytest
from bs4 import BeautifulSoup
from google.cloud import ndb
from werkzeug.test import Client

import backend
from backend.common.consts.event_type import EventType
from backend.common.consts.suggestion_state import SuggestionState
from backend.common.consts.webcast_type import WebcastType
from backend.common.models.account import Account
from backend.common.models.event import Event
from backend.common.models.suggestion import Suggestion
from backend.common.models.webcast import Webcast
from backend.web.handlers.tests.conftest import CapturedTemplate


@pytest.fixture(autouse=True)
def createEvent(ndb_client) -> None:
    with ndb_client.context():
        event = Event(
            id="2016necmp",
            name="New England District Championship",
            event_type_enum=EventType.DISTRICT_CMP,
            short_name="New England",
            event_short="necmp",
            year=2016,
            end_date=datetime(2016, 3, 27),
            official=False,
            city="Hartford",
            state_prov="CT",
            country="USA",
            venue="Some Venue",
            venue_address="Some Venue, Hartford, CT, USA",
            timezone_id="America/New_York",
            start_date=datetime(2016, 3, 24),
            webcast_json="",
            website="http://www.firstsv.org",
        )
        event.put()


@pytest.fixture
def login_user(ndb_client):
    with ndb_client.context():
        account = Account(
            email="test@tba.com",
            registered=True,
        )
        account_key = account.put()

    mock_user = Mock()
    mock_user.is_registered = True
    mock_user.api_read_keys = []
    mock_user.api_write_keys = []
    mock_user.mobile_clients = []
    mock_user.account_key = account_key

    with patch.object(
        backend.web.handlers.decorators, "current_user", return_value=mock_user
    ), patch.object(
        backend.web.handlers.suggestions, "current_user", return_value=mock_user
    ):
        yield mock_user


def assert_template_status(
    captured_templates: List[CapturedTemplate], status: str
) -> None:
    template = captured_templates[0][0]
    context = captured_templates[0][1]
    assert template.name == "suggestions/suggest_event_webcast.html"
    assert context["status"] == status


def test_login_redirect(web_client: Client) -> None:
    response = web_client.get("/suggest/event/webcast?event_key=2016necmp")
    assert response.status_code == 302
    assert urlparse(response.headers["Location"]).path == "/account/login"


def test_get_form_bad_event(login_user, web_client: Client) -> None:
    response = web_client.get("/suggest/event/webcast?event_key=2016asdf")
    assert response.status_code == 404


def test_get_form(login_user, web_client: Client) -> None:
    response = web_client.get("/suggest/event/webcast?event_key=2016necmp")
    assert response.status_code == 200

    soup = BeautifulSoup(response.data, "html.parser")
    form = soup.find("form", id="suggest_webcast")
    assert form is not None
    assert form["action"] == "/suggest/event/webcast"
    assert form["method"] == "post"

    csrf = form.find(attrs={"name": "csrf_token"})
    assert csrf is not None
    assert csrf["type"] == "hidden"
    assert csrf["value"] is not None

    event_key = form.find(attrs={"name": "event_key"})
    assert event_key is not None
    assert event_key["type"] == "hidden"
    assert event_key["value"] == "2016necmp"

    assert form.find(attrs={"name": "webcast_url"}) is not None
    assert form.find(attrs={"name": "webcast_date"}) is not None
    assert form.find("button", type="submit") is not None


def test_submit_no_event(
    login_user, ndb_client: ndb.Client, web_client: Client
) -> None:
    resp = web_client.post("/suggest/event/webcast", data={}, follow_redirects=True)
    assert resp.status_code == 404

    # Assert no suggestions were written
    with ndb_client.context():
        assert Suggestion.query().fetch() == []


def test_submit_empty_form(
    login_user,
    ndb_client: ndb.Client,
    web_client: Client,
    captured_templates: List[CapturedTemplate],
) -> None:
    resp = web_client.post(
        "/suggest/event/webcast", data={"event_key": "2016necmp"}, follow_redirects=True
    )
    assert resp.status_code == 200
    assert_template_status(captured_templates, "blank_webcast")

    # Assert the correct dialog shows
    soup = BeautifulSoup(resp.data, "html.parser")
    assert soup.find(id="blank_webcast-alert") is not None

    # Assert no suggestions were written
    with ndb_client.context():
        assert Suggestion.query().fetch() == []


def test_submit_bad_url(
    login_user,
    ndb_client: ndb.Client,
    web_client: Client,
    captured_templates: List[CapturedTemplate],
) -> None:
    resp = web_client.post(
        "/suggest/event/webcast",
        data={"event_key": "2016necmp", "webcast_url": "The Blue Alliance"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert_template_status(captured_templates, "invalid_url")

    # Assert the correct dialog shows
    soup = BeautifulSoup(resp.data, "html.parser")
    assert soup.find(id="invalid_url-alert") is not None

    # Assert no suggestions were written
    with ndb_client.context():
        assert Suggestion.query().fetch() == []


def test_submit_tba_url(
    login_user,
    ndb_client: ndb.Client,
    web_client: Client,
    captured_templates: List[CapturedTemplate],
) -> None:
    resp = web_client.post(
        "/suggest/event/webcast",
        data={"event_key": "2016necmp", "webcast_url": "http://thebluealliance.com"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert_template_status(captured_templates, "invalid_url")

    # Assert the correct dialog shows
    soup = BeautifulSoup(resp.data, "html.parser")
    assert soup.find(id="invalid_url-alert") is not None

    # Assert no suggestions were written
    with ndb_client.context():
        assert Suggestion.query().fetch() == []


def test_submit_webcast(
    login_user,
    ndb_client: ndb.Client,
    web_client: Client,
    captured_templates: List[CapturedTemplate],
) -> None:
    resp = web_client.post(
        "/suggest/event/webcast",
        data={
            "event_key": "2016necmp",
            "webcast_url": "https://twitch.tv/frcgamesense",
            "webcast_date": "",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert_template_status(captured_templates, "success")

    # Assert the correct dialog shows
    soup = BeautifulSoup(resp.data, "html.parser")
    assert soup.find(id="success-alert") is not None

    # Make sure the Suggestion gets created
    with ndb_client.context():
        suggestion = cast(Suggestion, Suggestion.query().fetch()[0])
        assert suggestion is not None
        assert suggestion.review_state == SuggestionState.REVIEW_PENDING
        assert suggestion.target_key == "2016necmp"
        assert suggestion.contents["webcast_url"] == "https://twitch.tv/frcgamesense"
        assert suggestion.contents.get("webcast_dict") == Webcast(
            type=WebcastType.TWITCH, channel="frcgamesense"
        )
