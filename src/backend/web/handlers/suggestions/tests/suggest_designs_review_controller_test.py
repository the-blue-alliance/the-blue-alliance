import re
from typing import List
from urllib.parse import urlparse

import pytest
from bs4 import BeautifulSoup
from google.cloud import ndb
from werkzeug.test import Client

from backend.common.consts.account_permission import AccountPermission
from backend.common.consts.media_type import MediaType
from backend.common.consts.suggestion_state import SuggestionState
from backend.common.models.media import Media
from backend.common.models.suggestion import Suggestion
from backend.common.models.team import Team
from backend.common.suggestions.suggestion_creator import (
    SuggestionCreationStatus,
    SuggestionCreator,
)


@pytest.fixture
def login_user_with_permission(login_user):
    login_user.permissions = [AccountPermission.REVIEW_DESIGNS]
    return login_user


def get_suggestion_queue(web_client: Client) -> List[str]:
    response = web_client.get("/suggest/cad/review")
    assert response.status_code == 200
    soup = BeautifulSoup(response.data, "html.parser")
    review_form = soup.find(id="review_designs")
    assert review_form is not None
    suggestions = review_form.find_all(class_="suggestion-item")
    queue = []
    for suggestion in suggestions:
        accept_button = suggestion.find(
            "input",
            attrs={
                "name": re.compile("accept_reject-.*"),
                "value": re.compile("accept::.*"),
            },
        )
        assert accept_button is not None
        reject_button = suggestion.find(
            "input",
            attrs={
                "name": re.compile("accept_reject-.*"),
                "value": re.compile("reject::.*"),
            },
        )
        assert reject_button is not None
        queue.append(accept_button["value"].split("::")[1])
    return queue


def createSuggestion(logged_in_user, ndb_client: ndb.Client) -> str:
    with ndb_client.context():
        status = SuggestionCreator.createTeamMediaSuggestion(
            logged_in_user.account_key,
            "https://grabcad.com/library/2016-148-robowranglers-1",
            "frc1124",
            "2016",
        )
        assert status[0] == SuggestionCreationStatus.SUCCESS
        return Suggestion.render_media_key_name(
            2016, "team", "frc1124", "grabcad", "2016-148-robowranglers-1"
        )


def test_login_redirect(web_client: Client) -> None:
    response = web_client.get("/suggest/cad/review")
    assert response.status_code == 302
    assert urlparse(response.headers["Location"]).path == "/account/login"


def test_no_permissions(login_user, web_client: Client) -> None:
    response = web_client.get("/suggest/cad/review")
    assert response.status_code == 401


def test_nothing_to_review(login_user_with_permission, web_client: Client) -> None:
    queue = get_suggestion_queue(web_client)
    assert queue == []


def test_accept_suggestion(
    login_user_with_permission, ndb_client: ndb.Client, web_client: Client
) -> None:
    suggestion_id = createSuggestion(login_user_with_permission, ndb_client)
    queue = get_suggestion_queue(web_client)
    assert queue == [suggestion_id]

    response = web_client.post(
        "/suggest/cad/review",
        data={
            f"accept_reject-{suggestion_id}": f"accept::{suggestion_id}",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200

    # Make sure the Media object gets created
    with ndb_client.context():
        media = Media.get_by_id(
            Media.render_key_name(MediaType.GRABCAD, "2016-148-robowranglers-1")
        )
        assert media is not None
        assert media.media_type_enum == MediaType.GRABCAD
        assert media.year == 2016
        assert ndb.Key(Team, "frc1124") in media.references

        # Make sure we mark the Suggestion as REVIEWED
        suggestion = Suggestion.get_by_id(suggestion_id)
        assert suggestion is not None
        assert suggestion.review_state == SuggestionState.REVIEW_ACCEPTED


def test_reject_suggestion(
    login_user_with_permission, ndb_client: ndb.Client, web_client: Client
) -> None:
    suggestion_id = createSuggestion(login_user_with_permission, ndb_client)
    queue = get_suggestion_queue(web_client)
    assert queue == [suggestion_id]

    response = web_client.post(
        "/suggest/cad/review",
        data={
            f"accept_reject-{suggestion_id}": f"reject::{suggestion_id}",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200

    # Make sure the Media object doesn't get created
    with ndb_client.context():
        medias = Media.query().fetch(keys_only=True)
        assert medias == []

        # Make sure we mark the Suggestion as REVIEWED
        suggestion = Suggestion.get_by_id(suggestion_id)
        assert suggestion is not None
        assert suggestion.review_state == SuggestionState.REVIEW_REJECTED


def test_fast_path_accept(
    login_user_with_permission, ndb_client: ndb.Client, web_client: Client
):
    suggestion_id = createSuggestion(login_user_with_permission, ndb_client)

    response = web_client.get(
        f"/suggest/cad/review?action=accept&id={suggestion_id}",
        follow_redirects=True,
    )
    assert response.status_code == 200

    # Make sure the Media object gets created
    with ndb_client.context():
        media = Media.get_by_id(
            Media.render_key_name(MediaType.GRABCAD, "2016-148-robowranglers-1")
        )
        assert media is not None
        assert media.media_type_enum == MediaType.GRABCAD
        assert media.year == 2016
        assert ndb.Key(Team, "frc1124") in media.references

        suggestion = Suggestion.get_by_id(suggestion_id)
        assert suggestion is not None
        assert suggestion.review_state == SuggestionState.REVIEW_ACCEPTED


def test_fast_path_reject(
    login_user_with_permission, ndb_client: ndb.Client, web_client: Client
) -> None:
    suggestion_id = createSuggestion(login_user_with_permission, ndb_client)

    response = web_client.get(
        f"/suggest/cad/review?action=reject&id={suggestion_id}",
        follow_redirects=True,
    )
    assert response.status_code == 200

    # Make sure the Media object gets created
    with ndb_client.context():
        media = Media.get_by_id(
            Media.render_key_name(MediaType.GRABCAD, "2016-148-robowranglers-1")
        )
        assert media is None

        suggestion = Suggestion.get_by_id(suggestion_id)
        assert suggestion is not None
        assert suggestion.review_state == SuggestionState.REVIEW_REJECTED


def test_fast_path_already_reviewed(
    login_user_with_permission, ndb_client: ndb.Client, web_client: Client
) -> None:
    suggestion_id = createSuggestion(login_user_with_permission, ndb_client)
    with ndb_client.context():
        suggestion = Suggestion.get_by_id(suggestion_id)
        assert suggestion is not None
        suggestion.review_state = SuggestionState.REVIEW_ACCEPTED
        suggestion.put()

    response = web_client.get(
        f"/suggest/cad/review?action=accept&id={suggestion_id}",
        follow_redirects=True,
    )
    assert response.status_code == 200


def test_fast_path_bad_id(login_user_with_permission, web_client: Client) -> None:
    response = web_client.get(
        "/suggest/cad/review?action=accept&id=abc123",
        follow_redirects=True,
    )
    assert response.status_code == 200
