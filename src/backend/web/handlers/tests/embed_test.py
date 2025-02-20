import json
import re
from urllib.parse import urlparse

from google.appengine.ext import ndb
from requests_mock import Mocker
from werkzeug import Client

from backend.common.consts.account_permission import AccountPermission
from backend.common.consts.media_type import MediaType
from backend.common.models.account import Account
from backend.common.models.media import Media

THUMBNAIL_URL = "scontent.cdninstagram.com/abc"


def create_media() -> Media:
    media = Media(
        media_type_enum=MediaType.INSTAGRAM_IMAGE,
        foreign_key="abc",
        id=Media.render_key_name(MediaType.INSTAGRAM_IMAGE, "abc"),
    )
    media.put()
    return media


def create_avatar() -> Media:
    avatar = Media(
        id=Media.render_key_name(MediaType.AVATAR, "avatar_2024_frc604"),
        media_type_enum=MediaType.AVATAR,
        foreign_key="avatar_2024_frc604",
        references=[ndb.Key("Team", "frc604")],
        year=2024,
        details_json=json.dumps(
            {
                "base64Image": "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"
            }
        ),
    )
    avatar.put()
    return avatar


def test_instagram_no_media_key(web_client: Client):
    resp = web_client.get("/instagram_oembed/")
    assert resp.status_code == 404


def test_instagram_no_referer(web_client: Client):
    media = create_media()

    resp = web_client.get(f"/instagram_oembed/{media.foreign_key}")
    assert resp.status_code == 403


def test_instagram_success(web_client: Client, requests_mock: Mocker):
    media = create_media()

    requests_mock.get(
        re.compile(".*instagram_oembed.*"),
        json={"thumbnail_url": THUMBNAIL_URL},
    )

    resp = web_client.get(
        f"/instagram_oembed/{media.foreign_key}",
        headers={"Referer": "thebluealliance.com"},
    )

    assert resp.status_code == 302
    assert urlparse(resp.headers["Location"]).path == THUMBNAIL_URL


def test_instagram_success_media_reviewer(
    login_user: Account, requests_mock, web_client
):
    login_user.permissions = [AccountPermission.REVIEW_MEDIA]

    requests_mock.get(
        re.compile(".*instagram_oembed.*"),
        json={"thumbnail_url": THUMBNAIL_URL},
    )

    resp = web_client.get(
        "/instagram_oembed/abc",
        headers={"Referer": "thebluealliance.com"},
    )

    assert resp.status_code == 302
    assert urlparse(resp.headers["Location"]).path == THUMBNAIL_URL


def test_nonexistent_avatar(web_client: Client):
    resp = web_client.get(
        "/avatar/2024/frc604.png",
        headers={"Referer": "thebluealliance.com"},
    )
    assert resp.status_code == 404


def test_avatar(web_client: Client):
    avatar = create_avatar()
    assert avatar.avatar_image_url == "/avatar/2024/frc604.png"

    resp = web_client.get(
        "/avatar/2024/frc604.png",
        headers={"Referer": "thebluealliance.com"},
    )
    assert resp.status_code == 200
    assert resp.content_type == "image/png"
    assert resp.cache_control.public
    assert (
        resp.cache_control.max_age and float(resp.cache_control.max_age) == 24 * 60 * 60
    )
