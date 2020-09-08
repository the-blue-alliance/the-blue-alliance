from typing import cast, List
from urllib.parse import urlparse

import pytest
from bs4 import BeautifulSoup
from google.cloud import ndb
from werkzeug.test import Client

from backend.common.consts.event_type import EventType
from backend.common.consts.media_type import MediaType
from backend.common.consts.suggestion_state import SuggestionState
from backend.common.models.event import Event
from backend.common.models.suggestion import Suggestion
from backend.common.models.suggestion_dict import SuggestionDict
from backend.web.handlers.tests.conftest import CapturedTemplate


@pytest.fixture(autouse=True)
def storeEvent(ndb_client: ndb.Client) -> None:
    with ndb_client.context():
        event = Event(
            id="2016nyny",
            event_type_enum=EventType.REGIONAL,
            name="NYC",
            event_short="NYC",
            year=2016,
        )
        event.put()


def assert_template_status(
    captured_templates: List[CapturedTemplate], status: str
) -> None:
    template = captured_templates[0][0]
    context = captured_templates[0][1]
    assert template.name == "suggestions/suggest_event_media.html"
    assert context["status"] == status


def test_login_redirect(web_client: Client) -> None:
    response = web_client.get("/suggest/event/media?event_key=2016nyny")
    assert response.status_code == 302
    assert urlparse(response.headers["Location"]).path == "/account/login"


def test_get_no_event(login_user, web_client: Client) -> None:
    response = web_client.get("/suggest/event/media")
    assert response.status_code == 404


def test_get_bad_event(login_user, web_client: Client) -> None:
    response = web_client.get("/suggest/event/media?event_key=2016foo")
    assert response.status_code == 404


def test_get_form(login_user, web_client: Client) -> None:
    response = web_client.get("/suggest/event/media?event_key=2016nyny")
    assert response.status_code == 200

    soup = BeautifulSoup(response.data, "html.parser")
    form = soup.find("form", id="suggest_media")
    assert form is not None
    assert form["action"] == "/suggest/event/media"
    assert form["method"] == "post"

    csrf = form.find(attrs={"name": "csrf_token"})
    assert csrf is not None
    assert csrf["type"] == "hidden"
    assert csrf["value"] is not None

    event_key = form.find(attrs={"name": "event_key"})
    assert event_key is not None
    assert event_key["type"] == "hidden"
    assert event_key["value"] == "2016nyny"

    assert form.find(attrs={"name": "media_url"}) is not None


def test_submit_no_data(login_user, ndb_client: ndb.Client, web_client: Client) -> None:
    resp = web_client.post("/suggest/event/media", data={}, follow_redirects=True)
    assert resp.status_code == 404

    # Assert no suggestions were written
    with ndb_client.context():
        assert Suggestion.query().fetch() == []


def test_submit_bad_event(
    login_user, ndb_client: ndb.Client, web_client: Client
) -> None:
    resp = web_client.post(
        "/suggest/event/media", data={"event_key": "2016foo"}, follow_redirects=True
    )
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
        "/suggest/event/media",
        data={"event_key": "2016nyny"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert_template_status(captured_templates, "bad_url")

    # Assert the correct dialog shows
    soup = BeautifulSoup(resp.data, "html.parser")
    assert soup.find(id="bad_url-alert") is not None

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
        "/suggest/event/media",
        data={"event_key": "2016nyny", "media_url": "asdf"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert_template_status(captured_templates, "bad_url")

    # Assert the correct dialog shows
    soup = BeautifulSoup(resp.data, "html.parser")
    assert soup.find(id="bad_url-alert") is not None

    # Assert no suggestions were written
    with ndb_client.context():
        assert Suggestion.query().fetch() == []


def test_suggest_media(
    login_user,
    ndb_client: ndb.Client,
    web_client: Client,
    captured_templates: List[CapturedTemplate],
) -> None:
    resp = web_client.post(
        "/suggest/event/media",
        data={
            "event_key": "2016nyny",
            "media_url": "https://www.youtube.com/watch?v=H-54KMwMKY0",
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
        assert suggestion.target_model == "event_media"
        assert suggestion.contents == SuggestionDict(
            year=2016,
            reference_type="event",
            reference_key="2016nyny",
            foreign_key="H-54KMwMKY0",
            is_social=False,
            media_type_enum=MediaType.YOUTUBE_VIDEO,
            site_name="YouTube Video",
        )
