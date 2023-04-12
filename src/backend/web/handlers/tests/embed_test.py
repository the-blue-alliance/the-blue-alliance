import re
from urllib.parse import urlparse

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

    resp = web_client.get("/instagram_oembed/abc")

    assert resp.status_code == 302
    assert urlparse(resp.headers["Location"]).path == THUMBNAIL_URL
