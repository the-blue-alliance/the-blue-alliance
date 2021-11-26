import re
from datetime import datetime
from typing import cast, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import pytest
from bs4 import BeautifulSoup
from google.appengine.ext import ndb
from pyre_extensions import none_throws
from werkzeug.test import Client

from backend.common.consts.account_permission import AccountPermission
from backend.common.consts.auth_type import AuthType
from backend.common.consts.event_type import EventType
from backend.common.consts.suggestion_state import SuggestionState
from backend.common.models.api_auth_access import ApiAuthAccess
from backend.common.models.event import Event
from backend.common.models.suggestion import Suggestion
from backend.common.suggestions.suggestion_creator import (
    SuggestionCreationStatus,
    SuggestionCreator,
)
from backend.web.handlers.conftest import get_inputs_from_form


@pytest.fixture(autouse=True)
def storeEvent(ndb_stub):
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


@pytest.fixture
def login_user_with_permission(login_user):
    login_user.permissions = [AccountPermission.REVIEW_APIWRITE]
    return login_user


def get_suggestion_queue_and_fields(
    web_client: Client, suggestion_id: Optional[int] = None
) -> Tuple[List[str], Dict]:
    response = web_client.get("/suggest/apiwrite/review")
    assert response.status_code == 200
    soup = BeautifulSoup(response.data, "html.parser")
    review_form = soup.find(id="review_apiwrite")
    assert review_form is not None
    suggestions = review_form.find_all(class_="suggestion-item")
    queue = []
    for suggestion in suggestions:
        suggestion_form = suggestion.find(
            "form",
            attrs={
                "id": re.compile("apiwrite_review_.*"),
            },
        )
        assert suggestion_form is not None
        queue.append(int(suggestion_form["id"].split("apiwrite_review_")[1]))

    inputs = None
    if suggestion_id:
        form = soup.find(id=f"apiwrite_review_{suggestion_id}")
        assert form is not None
        inputs = get_inputs_from_form(form)

    return queue, (inputs or {})


def createSuggestion(logged_in_user) -> int:
    status = SuggestionCreator.createApiWriteSuggestion(
        logged_in_user.account_key, "2016necmp", "Test", [AuthType.EVENT_MATCHES]
    )
    assert status == SuggestionCreationStatus.SUCCESS
    return none_throws(
        Suggestion.query(Suggestion.target_key == "2016necmp")
        .fetch(keys_only=True)[0]
        .id()
    )


def test_login_redirect(web_client: Client) -> None:
    response = web_client.get("/suggest/apiwrite/review")
    assert response.status_code == 302
    assert urlparse(response.headers["Location"]).path == "/account/login"


def test_no_permissions(login_user, web_client: Client) -> None:
    response = web_client.get("/suggest/apiwrite/review")
    assert response.status_code == 401


def test_nothing_to_review(login_user_with_permission, web_client: Client) -> None:
    queue, _ = get_suggestion_queue_and_fields(web_client)
    assert queue == []


def test_accespt_suggestion(
    login_user_with_permission, ndb_stub, web_client: Client
) -> None:
    suggestion_id = createSuggestion(login_user_with_permission)
    queue, form_fields = get_suggestion_queue_and_fields(web_client, suggestion_id)
    assert queue == [suggestion_id]
    assert form_fields is not {}

    form_fields["verdict"] = "accept"
    response = web_client.post(
        "/suggest/apiwrite/review",
        data=form_fields,
        follow_redirects=True,
    )
    assert response.status_code == 200

    # Make sure the ApiWrite object gets created
    auth = cast(ApiAuthAccess, ApiAuthAccess.query().fetch()[0])
    assert auth is not None
    assert auth.owner == login_user_with_permission.account_key
    assert auth.event_list == [ndb.Key(Event, "2016necmp")]
    assert auth.auth_types_enum == [AuthType.EVENT_MATCHES]
    assert auth.secret is not None
    assert auth.expiration is not None

    # Make sure we mark the Suggestion as REVIEWED
    suggestion = Suggestion.get_by_id(suggestion_id)
    assert suggestion is not None
    assert suggestion.review_state == SuggestionState.REVIEW_ACCEPTED


def test_reject_suggestion(
    login_user_with_permission, ndb_stub, web_client: Client
) -> None:
    suggestion_id = createSuggestion(login_user_with_permission)
    queue, form_fields = get_suggestion_queue_and_fields(web_client, suggestion_id)
    assert queue == [suggestion_id]
    assert form_fields is not {}

    form_fields["verdict"] = "reject"
    response = web_client.post(
        "/suggest/apiwrite/review",
        data=form_fields,
        follow_redirects=True,
    )
    assert response.status_code == 200

    auths = ApiAuthAccess.query().fetch()
    assert auths == []

    # Make sure we mark the Suggestion as REJECTED
    suggestion = Suggestion.get_by_id(suggestion_id)
    assert suggestion is not None
    assert suggestion.review_state == SuggestionState.REVIEW_REJECTED


def test_existing_auth_keys(
    login_user_with_permission, ndb_stub, web_client: Client
) -> None:
    existing_auth = ApiAuthAccess(
        id="tEsT_id_0",
        secret="321tEsTsEcReT",
        description="test",
        event_list=[ndb.Key(Event, "2016necmp")],
        auth_types_enum=[AuthType.EVENT_TEAMS],
    )
    existing_auth.put()

    suggestion_id = createSuggestion(login_user_with_permission)
    queue, form_fields = get_suggestion_queue_and_fields(web_client, suggestion_id)
    assert queue == [suggestion_id]
    assert form_fields is not {}

    form_fields["verdict"] = "accept"
    response = web_client.post(
        "/suggest/apiwrite/review",
        data=form_fields,
        follow_redirects=True,
    )
    assert response.status_code == 200

    auths = ApiAuthAccess.query().fetch()
    assert len(auths) == 2


def test_accept_suggestion_with_different_auth_types(
    login_user_with_permission, ndb_stub, web_client: Client
) -> None:
    suggestion_id = createSuggestion(login_user_with_permission)
    queue, form_fields = get_suggestion_queue_and_fields(web_client, suggestion_id)
    assert queue == [suggestion_id]
    assert form_fields is not {}

    form_fields["auth_types"] = [AuthType.MATCH_VIDEO.value, AuthType.EVENT_TEAMS.value]
    form_fields["verdict"] = "accept"
    response = web_client.post(
        "/suggest/apiwrite/review",
        data=form_fields,
        follow_redirects=True,
    )
    assert response.status_code == 200

    # Make sure the ApiWrite object gets created
    auth = cast(ApiAuthAccess, ApiAuthAccess.query().fetch()[0])
    assert auth is not None
    assert auth.owner == login_user_with_permission.account_key
    assert auth.event_list == [ndb.Key(Event, "2016necmp")]
    assert set(auth.auth_types_enum) == {
        AuthType.EVENT_TEAMS.value,
        AuthType.MATCH_VIDEO.value,
    }
    assert auth.secret is not None
    assert auth.expiration is not None
