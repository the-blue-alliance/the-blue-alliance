import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

import pytest
from bs4 import BeautifulSoup
from google.cloud import ndb
from werkzeug.test import Client

from backend.common.consts.account_permission import AccountPermission
from backend.common.consts.event_type import EventType
from backend.common.consts.suggestion_state import SuggestionState
from backend.common.models.event import Event
from backend.common.models.suggestion import Suggestion
from backend.common.models.webcast import Webcast, WebcastType
from backend.common.suggestions.suggestion_creator import (
    SuggestionCreationStatus,
    SuggestionCreator,
)
from backend.web.handlers.conftest import get_inputs_from_form


@pytest.fixture(autouse=True)
def create_event(ndb_client: ndb.Client) -> None:
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
            webcast_json="",
            website="http://www.firstsv.org",
        )
        event.put()


@pytest.fixture
def login_user_with_permission(login_user):
    login_user.permissions = [AccountPermission.REVIEW_MEDIA]
    return login_user


def get_suggestion_queue_and_fields(
    web_client: Client, form_id: Optional[str] = None
) -> Tuple[List[str], Dict]:
    response = web_client.get("/suggest/event/webcast/review")
    assert response.status_code == 200
    soup = BeautifulSoup(response.data, "html.parser")
    review_form = soup.find(id="review_webcasts")
    assert review_form is not None
    suggestions = review_form.find_all(id=re.compile("review_.*"))
    queue = []
    for suggestion in suggestions:
        queue.append(suggestion["id"].split("review_")[1])

    inputs = None
    if form_id:
        form = soup.find(id=form_id)
        assert form is not None
        inputs = get_inputs_from_form(form)

    return queue, (inputs or {})


def createSuggestion(logged_in_user, ndb_client: ndb.Client) -> str:
    with ndb_client.context():
        status = SuggestionCreator.createEventWebcastSuggestion(
            logged_in_user.account_key,
            "https://twitch.tv/frcgamesense",
            "",
            "2016necmp",
        )
        assert status == SuggestionCreationStatus.SUCCESS
        return "webcast_2016necmp_twitch_frcgamesense_None"


def test_login_redirect(web_client: Client) -> None:
    response = web_client.get("/suggest/event/webcast/review")
    assert response.status_code == 302
    assert urlparse(response.headers["Location"]).path == "/account/login"


def test_no_permissions(login_user, web_client: Client) -> None:
    response = web_client.get("/suggest/event/webcast/review")
    assert response.status_code == 401


def test_nothing_to_review(login_user_with_permission, web_client: Client) -> None:
    queue, _ = get_suggestion_queue_and_fields(web_client)
    assert queue == []


def test_reject_all(
    login_user_with_permission, web_client: Client, ndb_client: ndb.Client
) -> None:
    suggestion_id = createSuggestion(login_user_with_permission, ndb_client)
    queue, reject_fields = get_suggestion_queue_and_fields(
        web_client, "reject_all_2016necmp"
    )
    assert queue == [suggestion_id]
    assert reject_fields is not {}

    reject_fields["verdict"] = "reject_all"
    response = web_client.post(
        "/suggest/event/webcast/review",
        data=reject_fields,
        follow_redirects=True,
    )
    assert response.status_code == 200

    with ndb_client.context():
        # Make sure we mark the Suggestion as REVIEWED
        suggestion = Suggestion.get_by_id(suggestion_id)
        assert suggestion is not None
        assert suggestion.review_state == SuggestionState.REVIEW_REJECTED

        # Make sure the Event has no webcasts
        event = Event.get_by_id("2016necmp")
        assert event is not None
        assert event.webcast == []


def test_accept_with_default_details(
    login_user_with_permission, web_client: Client, ndb_client: ndb.Client
) -> None:
    suggestion_id = createSuggestion(login_user_with_permission, ndb_client)
    queue, form_fields = get_suggestion_queue_and_fields(
        web_client, f"review_{suggestion_id}"
    )
    assert queue == [suggestion_id]
    assert form_fields is not {}

    form_fields["verdict"] = "accept"
    response = web_client.post(
        "/suggest/event/webcast/review",
        data=form_fields,
        follow_redirects=True,
    )
    assert response.status_code == 200

    with ndb_client.context():
        # Make sure we mark the Suggestion as REVIEWED
        suggestion = Suggestion.get_by_id(suggestion_id)
        assert suggestion is not None
        assert suggestion.review_state == SuggestionState.REVIEW_ACCEPTED

        # Make sure the Event has a webcast
        event = Event.get_by_id("2016necmp")
        assert event is not None
        assert event.webcast == [
            Webcast(type=WebcastType.TWITCH, channel="frcgamesense")
        ]


def test_accept_with_different_details(
    login_user_with_permission, web_client: Client, ndb_client: ndb.Client
) -> None:
    suggestion_id = createSuggestion(login_user_with_permission, ndb_client)
    queue, form_fields = get_suggestion_queue_and_fields(
        web_client, f"review_{suggestion_id}"
    )
    assert queue == [suggestion_id]
    assert form_fields is not {}

    form_fields["webcast_type"] = "youtube"
    form_fields["webcast_channel"] = "foobar"
    form_fields["webcast_file"] = "meow"
    form_fields["verdict"] = "accept"

    form_fields["verdict"] = "accept"
    response = web_client.post(
        "/suggest/event/webcast/review",
        data=form_fields,
        follow_redirects=True,
    )
    assert response.status_code == 200

    with ndb_client.context():
        # Make sure we mark the Suggestion as REVIEWED
        suggestion = Suggestion.get_by_id(suggestion_id)
        assert suggestion is not None
        assert suggestion.review_state == SuggestionState.REVIEW_ACCEPTED

        # Make sure the Event has a webcast
        event = Event.get_by_id("2016necmp")
        assert event is not None
        assert event.webcast == [
            Webcast(
                type=WebcastType.YOUTUBE,
                channel="foobar",
                file="meow",
            )
        ]


def test_reject_single_webcast(
    login_user_with_permission, web_client: Client, ndb_client: ndb.Client
) -> None:
    suggestion_id = createSuggestion(login_user_with_permission, ndb_client)
    queue, form_fields = get_suggestion_queue_and_fields(
        web_client, f"review_{suggestion_id}"
    )
    assert queue == [suggestion_id]
    assert form_fields is not {}

    form_fields["verdict"] = "reject"
    response = web_client.post(
        "/suggest/event/webcast/review",
        data=form_fields,
        follow_redirects=True,
    )
    assert response.status_code == 200

    with ndb_client.context():
        # Make sure we mark the Suggestion as REVIEWED
        suggestion = Suggestion.get_by_id(suggestion_id)
        assert suggestion is not None
        assert suggestion.review_state == SuggestionState.REVIEW_REJECTED

        # Make sure the Event has no webcasts
        event = Event.get_by_id("2016necmp")
        assert event is not None
        assert event.webcast == []
