import re
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

import pytest
from bs4 import BeautifulSoup
from pyre_extensions import none_throws
from werkzeug.test import Client

from backend.common.consts.account_permission import AccountPermission
from backend.common.consts.suggestion_state import SuggestionState
from backend.common.models.event import Event
from backend.common.models.suggestion import Suggestion
from backend.common.suggestions.suggestion_creator import (
    SuggestionCreationStatus,
    SuggestionCreator,
)
from backend.web.handlers.conftest import get_inputs_from_form


@pytest.fixture
def login_user_with_permission(login_user):
    login_user.permissions = [AccountPermission.REVIEW_OFFSEASON_EVENTS]
    return login_user


def get_suggestion_queue_and_fields(
    web_client: Client, form_id: Optional[str] = None
) -> Tuple[List[str], Dict]:
    response = web_client.get("/suggest/offseason/review")
    assert response.status_code == 200
    soup = BeautifulSoup(response.data, "html.parser")
    review_form = soup.find(id="review_offseasons")
    assert review_form is not None
    suggestions = review_form.find_all(id=re.compile("review_.*"))
    queue = []
    for suggestion in suggestions:
        queue.append(int(suggestion["id"].split("review_")[1]))

    inputs = None
    if form_id:
        form = soup.find(id=form_id)
        assert form is not None
        inputs = get_inputs_from_form(form)

    return queue, (inputs or {})


def createSuggestion(logged_in_user) -> int:
    status = SuggestionCreator.createOffseasonEventSuggestion(
        logged_in_user.account_key,
        "Test Event",
        "2016-10-12",
        "2016-10-13",
        "http://foo.bar.com",
        "Venue Name",
        "123 Fake St",
        "New York",
        "NY",
        "USA",
    )
    assert status[0] == SuggestionCreationStatus.SUCCESS
    return none_throws(Suggestion.query().fetch(keys_only=True)[0].id())


def test_login_redirect(web_client: Client) -> None:
    response = web_client.get("/suggest/offseason/review")
    assert response.status_code == 302
    assert urlparse(response.headers["Location"]).path == "/account/login"


def test_no_permissions(login_user, web_client: Client) -> None:
    response = web_client.get("/suggest/offseason/review")
    assert response.status_code == 401


def test_nothing_to_review(login_user_with_permission, web_client: Client) -> None:
    queue, _ = get_suggestion_queue_and_fields(web_client)
    assert queue == []


def test_accept_suggestion(
    login_user_with_permission,
    web_client: Client,
    ndb_stub,
    taskqueue_stub,
) -> None:
    suggestion_id = createSuggestion(login_user_with_permission)
    queue, form_fields = get_suggestion_queue_and_fields(
        web_client, f"review_{suggestion_id}"
    )
    assert queue == [suggestion_id]
    assert form_fields is not {}

    form_fields["event_short"] = "test"
    form_fields["verdict"] = "accept"
    response = web_client.post(
        "/suggest/offseason/review",
        data=form_fields,
        follow_redirects=True,
    )
    assert response.status_code == 200

    suggestion = Suggestion.get_by_id(suggestion_id)
    assert suggestion is not None
    assert suggestion.review_state == SuggestionState.REVIEW_ACCEPTED

    event = Event.get_by_id("2016test")
    assert event is not None


def test_reject_suggestion(
    login_user_with_permission, web_client: Client, ndb_stub
) -> None:
    suggestion_id = createSuggestion(login_user_with_permission)
    queue, form_fields = get_suggestion_queue_and_fields(
        web_client, f"review_{suggestion_id}"
    )
    assert queue == [suggestion_id]
    assert form_fields is not {}

    form_fields["event_short"] = "test"
    form_fields["verdict"] = "reject"
    response = web_client.post(
        "/suggest/offseason/review",
        data=form_fields,
        follow_redirects=True,
    )
    assert response.status_code == 200

    suggestion = Suggestion.get_by_id(suggestion_id)
    assert suggestion is not None
    assert suggestion.review_state == SuggestionState.REVIEW_REJECTED

    event = Event.get_by_id("2016test")
    assert event is None
