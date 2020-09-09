from datetime import datetime
from typing import cast, List
from urllib.parse import urlparse

import pytest
from bs4 import BeautifulSoup
from google.cloud import ndb
from werkzeug.test import Client

from backend.common.consts.auth_type import AuthType, WRITE_TYPE_NAMES
from backend.common.consts.event_type import EventType
from backend.common.consts.suggestion_state import SuggestionState
from backend.common.models.event import Event
from backend.common.models.suggestion import Suggestion
from backend.common.models.suggestion_dict import SuggestionDict
from backend.web.handlers.tests.conftest import CapturedTemplate


@pytest.fixture(autouse=True)
def createEvent(ndb_client: ndb.Client) -> None:
    with ndb_client.context():
        event = Event(
            id="2016necmp",
            name="New England District Championship",
            event_type_enum=EventType.OFFSEASON,
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
            webcast_json='[{"type": "twitch", "channel": "frcgamesense"}]',
            website="http://www.firstsv.org",
        )
        event.put()


def assert_template_status(
    captured_templates: List[CapturedTemplate], status: str
) -> None:
    template = captured_templates[0][0]
    context = captured_templates[0][1]
    assert template.name == "suggestions/suggest_apiwrite.html"
    assert context["status"] == status


def test_login_redirect(web_client: Client) -> None:
    response = web_client.get("/request/apiwrite")
    assert response.status_code == 302
    assert urlparse(response.headers["Location"]).path == "/account/login"


def test_get_form(login_user, web_client: Client) -> None:
    response = web_client.get("/request/apiwrite")
    assert response.status_code == 200

    soup = BeautifulSoup(response.data, "html.parser")
    form = soup.find("form", id="suggest_apiwrite")
    assert form is not None
    assert form["action"] == "/request/apiwrite"
    assert form["method"] == "post"

    csrf = form.find(attrs={"name": "csrf_token"})
    assert csrf is not None
    assert csrf["type"] == "hidden"
    assert csrf["value"] is not None

    assert form.find(attrs={"name": "event_key"}) is not None
    assert form.find(attrs={"name": "role"}) is not None
    assert len(form.find_all(attrs={"name": "auth_types"})) == len(WRITE_TYPE_NAMES)


def test_submit_no_data(login_user, ndb_client: ndb.Client, web_client: Client) -> None:
    resp = web_client.post("/request/apiwrite", data={}, follow_redirects=True)
    assert resp.status_code == 404


def test_submit_empty_form(
    login_user,
    ndb_client: ndb.Client,
    web_client: Client,
    captured_templates: List[CapturedTemplate],
) -> None:
    resp = web_client.post(
        "/request/apiwrite", data={"event_key": "2016necmp"}, follow_redirects=True
    )
    assert resp.status_code == 200
    assert_template_status(captured_templates, "no_affiliation")

    # Assert the correct dialog shows
    soup = BeautifulSoup(resp.data, "html.parser")
    assert soup.find(id="no_affiliation-alert") is not None

    # Assert no suggestions were written
    with ndb_client.context():
        assert Suggestion.query().fetch() == []


def test_submit_bad_event(
    login_user,
    ndb_client: ndb.Client,
    web_client: Client,
    captured_templates: List[CapturedTemplate],
) -> None:
    resp = web_client.post(
        "/request/apiwrite",
        data={"event_key": "2016foo", "role": "Test Code"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert_template_status(captured_templates, "bad_event")

    # Assert the correct dialog shows
    soup = BeautifulSoup(resp.data, "html.parser")
    assert soup.find(id="bad_event-alert") is not None

    # Assert no suggestions were written
    with ndb_client.context():
        assert Suggestion.query().fetch() == []


def test_suggest_api_write(
    login_user,
    ndb_client: ndb.Client,
    web_client: Client,
    captured_templates: List[CapturedTemplate],
):
    resp = web_client.post(
        "/request/apiwrite",
        data={
            "event_key": "2016necmp",
            "role": "Test Code",
            "auth_types": [int(AuthType.MATCH_VIDEO), int(AuthType.EVENT_TEAMS)],
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
        assert suggestion.target_model == "api_auth_access"
        assert suggestion.contents == SuggestionDict(
            event_key="2016necmp",
            affiliation="Test Code",
            auth_types=[AuthType.MATCH_VIDEO, AuthType.EVENT_TEAMS],
        )
