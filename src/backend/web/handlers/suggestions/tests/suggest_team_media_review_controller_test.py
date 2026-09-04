import json
import re
from typing import List
from unittest.mock import patch
from urllib.parse import urlparse

import pytest
from bs4 import BeautifulSoup
from google.appengine.ext import ndb
from werkzeug.test import Client

from backend.common.consts.account_permission import AccountPermission
from backend.common.consts.media_type import MediaType
from backend.common.consts.suggestion_state import SuggestionState
from backend.common.futures import InstantFuture
from backend.common.models.media import Media
from backend.common.models.suggestion import Suggestion
from backend.common.models.team import Team
from backend.common.suggestions.media_parser import MediaParser
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
    ).get_result()
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


def test_instagram_suggestion_renders_embed(
    login_user_with_permission,
    web_client: Client,
) -> None:
    status = SuggestionCreator.createTeamMediaSuggestion(
        login_user_with_permission.account_key,
        "https://www.instagram.com/p/abc123/",
        "frc1124",
        "2024",
    ).get_result()
    assert status[0] == SuggestionCreationStatus.SUCCESS

    response = web_client.get("/suggest/team/media/review")
    assert response.status_code == 200
    soup = BeautifulSoup(response.data, "html.parser")

    # Verify Instagram embed blockquote is rendered
    blockquote = soup.find("blockquote", class_="instagram-media")
    assert blockquote is not None
    assert (
        blockquote.get("data-instgrm-permalink")
        == "https://www.instagram.com/p/abc123/"
    )

    # Verify embed.js script is included
    embed_script = soup.find("script", attrs={"src": re.compile("instagram.com/embed")})
    assert embed_script is not None


def createSmugmugSuggestion(logged_in_user, media_dict) -> None:
    with patch.object(
        MediaParser, "_parse_smugmug", return_value=InstantFuture(media_dict)
    ):
        status = SuggestionCreator.createTeamMediaSuggestion(
            logged_in_user.account_key,
            "https://nefirst.smugmug.com/2026-FIRST-AGE/2026-CMP-BAE",
            "frc1124",
            "2026",
        ).get_result()
    assert status[0] == SuggestionCreationStatus.SUCCESS


def test_smugmug_photo_suggestion_renders_image(
    login_user_with_permission,
    web_client: Client,
) -> None:
    createSmugmugSuggestion(
        login_user_with_permission,
        {
            "media_type_enum": MediaType.SMUGMUG_PHOTO,
            "is_social": False,
            "foreign_key": "xxrbgK6",
            "site_name": "SmugMug Photo",
            "details_json": json.dumps(
                {
                    "title": "Robot on the field",
                    "caption": "",
                    "web_uri": "https://nefirst.smugmug.com/2026-FIRST-AGE/2026-CMP-BAE/i-xxrbgK6",
                    "image_url": "https://photos.smugmug.com/L/x-L.jpg",
                    "image_url_med": "https://photos.smugmug.com/M/x-M.jpg",
                    "image_url_sm": "https://photos.smugmug.com/S/x-S.jpg",
                }
            ),
        },
    )

    response = web_client.get("/suggest/team/media/review")
    assert response.status_code == 200
    soup = BeautifulSoup(response.data, "html.parser")

    thumbnail = soup.find(
        "a", class_="gallery", href="https://photos.smugmug.com/L/x-L.jpg"
    )
    assert thumbnail is not None
    assert "https://photos.smugmug.com/M/x-M.jpg" in thumbnail.find("span")["style"]

    caption = soup.find(
        "a",
        href="https://nefirst.smugmug.com/2026-FIRST-AGE/2026-CMP-BAE/i-xxrbgK6",
    )
    assert caption is not None
    assert caption.text == "Robot on the field"

    # A SmugMug photo is an image type, so it can be made the preferred image
    assert soup.find("input", attrs={"name": "preferred_keys[]"}) is not None


def test_accept_smugmug_photo_as_preferred(
    login_user_with_permission,
    ndb_stub,
    web_client: Client,
    taskqueue_stub,
) -> None:
    createSmugmugSuggestion(
        login_user_with_permission,
        {
            "media_type_enum": MediaType.SMUGMUG_PHOTO,
            "is_social": False,
            "foreign_key": "xxrbgK6",
            "site_name": "SmugMug Photo",
            "details_json": json.dumps(
                {
                    "title": "Robot on the field",
                    "caption": "",
                    "web_uri": "https://nefirst.smugmug.com/2026-FIRST-AGE/2026-CMP-BAE/i-xxrbgK6",
                    "image_url": "https://photos.smugmug.com/L/x-L.jpg",
                    "image_url_med": "https://photos.smugmug.com/M/x-M.jpg",
                    "image_url_sm": "https://photos.smugmug.com/S/x-S.jpg",
                }
            ),
        },
    )
    suggestion_id = Suggestion.render_media_key_name(
        2026, "team", "frc1124", "smugmug-photo", "xxrbgK6"
    )

    response = web_client.post(
        "/suggest/team/media/review",
        data={
            f"accept_reject-{suggestion_id}": f"accept::{suggestion_id}",
            "preferred_keys[]": [f"preferred::{suggestion_id}"],
        },
        follow_redirects=True,
    )
    assert response.status_code == 200

    media = Media.get_by_id(Media.render_key_name(MediaType.SMUGMUG_PHOTO, "xxrbgK6"))
    assert media is not None
    assert media.is_image is True
    assert ndb.Key(Team, "frc1124") in media.references
    assert ndb.Key(Team, "frc1124") in media.preferred_references


def test_smugmug_album_is_not_preferrable(
    login_user_with_permission,
    web_client: Client,
) -> None:
    createSmugmugSuggestion(
        login_user_with_permission,
        {
            "media_type_enum": MediaType.SMUGMUG_ALBUM,
            "is_social": False,
            "foreign_key": "4RWMLM",
            "site_name": "SmugMug Album",
            "details_json": json.dumps(
                {
                    "title": "2026 FIRST Championship - BAE Systems",
                    "web_uri": "https://nefirst.smugmug.com/2026-FIRST-AGE/2026-CMP-BAE",
                    "image_count": 81,
                    "cover_url": "https://photos.smugmug.com/L/cover-L.png",
                    "cover_url_med": "https://photos.smugmug.com/M/cover-M.png",
                    "cover_url_sm": "https://photos.smugmug.com/S/cover-S.png",
                }
            ),
        },
    )

    response = web_client.get("/suggest/team/media/review")
    assert response.status_code == 200
    soup = BeautifulSoup(response.data, "html.parser")
    assert soup.find("input", attrs={"name": "preferred_keys[]"}) is None


def test_smugmug_album_suggestion_renders_cover(
    login_user_with_permission,
    web_client: Client,
) -> None:
    createSmugmugSuggestion(
        login_user_with_permission,
        {
            "media_type_enum": MediaType.SMUGMUG_ALBUM,
            "is_social": False,
            "foreign_key": "4RWMLM",
            "site_name": "SmugMug Album",
            "details_json": json.dumps(
                {
                    "title": "2026 FIRST Championship - BAE Systems",
                    "web_uri": "https://nefirst.smugmug.com/2026-FIRST-AGE/2026-CMP-BAE",
                    "image_count": 81,
                    "cover_url": "https://photos.smugmug.com/L/cover-L.png",
                    "cover_url_med": "https://photos.smugmug.com/M/cover-M.png",
                    "cover_url_sm": "https://photos.smugmug.com/S/cover-S.png",
                }
            ),
        },
    )

    response = web_client.get("/suggest/team/media/review")
    assert response.status_code == 200
    soup = BeautifulSoup(response.data, "html.parser")

    links = soup.find_all(
        "a", href="https://nefirst.smugmug.com/2026-FIRST-AGE/2026-CMP-BAE"
    )
    assert len(links) == 2

    cover, caption = links
    assert "https://photos.smugmug.com/M/cover-M.png" in cover.find("span")["style"]
    assert caption.text == "2026 FIRST Championship - BAE Systems"
    assert "81 photos" in caption.parent.text
