import re
from typing import List
from urllib.parse import urlparse

import pytest
from bs4 import BeautifulSoup
from google.appengine.ext import ndb
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
    login_user.permissions = [AccountPermission.REVIEW_MEDIA]
    return login_user


def get_suggestion_queue(web_client: Client) -> List[str]:
    response = web_client.get("/suggest/team/media/review")
    assert response.status_code == 200
    soup = BeautifulSoup(response.data, "html.parser")
    review_form = soup.find(id="review_media")
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
        year = suggestion.find("input", attrs={"name": re.compile("year-.*")})
        assert year is not None
        queue.append(accept_button["value"].split("::")[1])
    return queue


def createSuggestion(logged_in_user) -> str:
    status = SuggestionCreator.createTeamMediaSuggestion(
        logged_in_user.account_key, "http://imgur.com/foobar", "frc1124", "2016"
    )
    assert status[0] == SuggestionCreationStatus.SUCCESS
    return Suggestion.render_media_key_name(2016, "team", "frc1124", "imgur", "foobar")


def test_login_redirect(web_client: Client) -> None:
    response = web_client.get("/suggest/team/media/review")
    assert response.status_code == 302
    assert urlparse(response.headers["Location"]).path == "/account/login"


def test_no_permissions(login_user, web_client: Client) -> None:
    response = web_client.get("/suggest/team/media/review")
    assert response.status_code == 401


def test_nothing_to_review(login_user_with_permission, web_client: Client) -> None:
    queue = get_suggestion_queue(web_client)
    assert queue == []


def test_accept_suggestion(
    login_user_with_permission,
    ndb_stub,
    web_client: Client,
    taskqueue_stub,
) -> None:
    suggestion_id = createSuggestion(login_user_with_permission)
    queue = get_suggestion_queue(web_client)
    assert queue == [suggestion_id]

    response = web_client.post(
        "/suggest/team/media/review",
        data={
            f"accept_reject-{suggestion_id}": f"accept::{suggestion_id}",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200

    suggestion = Suggestion.get_by_id(suggestion_id)
    assert suggestion is not None
    assert suggestion.review_state == SuggestionState.REVIEW_ACCEPTED

    media = Media.get_by_id(Media.render_key_name(MediaType.IMGUR, "foobar"))
    assert media is not None
    assert media.year == 2016
    assert media.foreign_key == "foobar"
    assert media.media_type_enum == MediaType.IMGUR
    assert ndb.Key(Team, "frc1124") in media.references
    assert media.preferred_references == []


def test_accept_suggestion_change_year(
    login_user_with_permission,
    ndb_stub,
    web_client: Client,
    taskqueue_stub,
) -> None:
    suggestion_id = createSuggestion(login_user_with_permission)
    queue = get_suggestion_queue(web_client)
    assert queue == [suggestion_id]

    response = web_client.post(
        "/suggest/team/media/review",
        data={
            f"accept_reject-{suggestion_id}": f"accept::{suggestion_id}",
            f"year-{suggestion_id}": "2017",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200

    suggestion = Suggestion.get_by_id(suggestion_id)
    assert suggestion is not None
    assert suggestion.review_state == SuggestionState.REVIEW_ACCEPTED

    media = Media.get_by_id(Media.render_key_name(MediaType.IMGUR, "foobar"))
    assert media is not None
    assert media.year == 2017
    assert media.foreign_key == "foobar"
    assert media.media_type_enum == MediaType.IMGUR
    assert ndb.Key(Team, "frc1124") in media.references
    assert media.preferred_references == []


def test_accept_suggestion_as_preferred(
    login_user_with_permission,
    ndb_stub,
    web_client: Client,
    taskqueue_stub,
) -> None:
    suggestion_id = createSuggestion(login_user_with_permission)
    queue = get_suggestion_queue(web_client)
    assert queue == [suggestion_id]

    response = web_client.post(
        "/suggest/team/media/review",
        data={
            f"accept_reject-{suggestion_id}": f"accept::{suggestion_id}",
            "preferred_keys[]": [f"preferred::{suggestion_id}"],
        },
        follow_redirects=True,
    )
    assert response.status_code == 200

    suggestion = Suggestion.get_by_id(suggestion_id)
    assert suggestion is not None
    assert suggestion.review_state == SuggestionState.REVIEW_ACCEPTED

    media = Media.get_by_id(Media.render_key_name(MediaType.IMGUR, "foobar"))
    assert media is not None
    assert media.year == 2016
    assert media.foreign_key == "foobar"
    assert media.media_type_enum == MediaType.IMGUR
    assert ndb.Key(Team, "frc1124") in media.references
    assert ndb.Key(Team, "frc1124") in media.preferred_references


def test_accept_suggestion_as_preferred_and_replace(
    login_user_with_permission,
    ndb_stub,
    web_client: Client,
    taskqueue_stub,
) -> None:
    # Create an existing preferred media
    existing_preferred = Media(
        id=Media.render_key_name(MediaType.IMGUR, "baz"),
        foreign_key="baz",
        media_type_enum=MediaType.IMGUR,
        year=2016,
        preferred_references=[ndb.Key(Team, "frc1124")],
    )
    existing_preferred.put()

    suggestion_id = createSuggestion(login_user_with_permission)
    queue = get_suggestion_queue(web_client)
    assert queue == [suggestion_id]

    response = web_client.post(
        "/suggest/team/media/review",
        data={
            f"accept_reject-{suggestion_id}": f"accept::{suggestion_id}",
            "preferred_keys[]": [f"preferred::{suggestion_id}"],
            f"replace-preferred-{suggestion_id}": existing_preferred.key_name,
        },
        follow_redirects=True,
    )
    assert response.status_code == 200

    suggestion = Suggestion.get_by_id(suggestion_id)
    assert suggestion is not None
    assert suggestion.review_state == SuggestionState.REVIEW_ACCEPTED

    media = Media.get_by_id(Media.render_key_name(MediaType.IMGUR, "foobar"))
    assert media is not None
    assert media.year == 2016
    assert media.foreign_key == "foobar"
    assert media.media_type_enum == MediaType.IMGUR
    assert ndb.Key(Team, "frc1124") in media.references
    assert ndb.Key(Team, "frc1124") in media.preferred_references

    old_preferred_media = Media.get_by_id(existing_preferred.key_name)
    assert old_preferred_media is not None
    assert ndb.Key(Team, "frc1124") not in old_preferred_media.preferred_references


def test_reject_suggestion(
    login_user_with_permission, ndb_stub, web_client: Client
) -> None:
    suggestion_id = createSuggestion(login_user_with_permission)
    queue = get_suggestion_queue(web_client)
    assert queue == [suggestion_id]

    response = web_client.post(
        "/suggest/team/media/review",
        data={
            f"accept_reject-{suggestion_id}": f"reject::{suggestion_id}",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200

    suggestion = Suggestion.get_by_id(suggestion_id)
    assert suggestion is not None
    assert suggestion.review_state == SuggestionState.REVIEW_REJECTED

    # Verify no medias are created
    medias = Media.query().fetch()
    assert medias == []
