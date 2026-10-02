import json
from typing import Any

import orjson
import pytest
from google.appengine.api import datastore_errors
from google.appengine.ext import ndb

from backend.common.consts.media_tag import MediaTag
from backend.common.consts.media_type import MediaType
from backend.common.models.media import Media
from backend.common.models.team import Team


@pytest.mark.parametrize("key", ["youtube_asdf", "imgur_xyz"])
def test_valid_key_names(key: str) -> None:
    assert Media.validate_key_name(key) is True


@pytest.mark.parametrize("key", ["imgurabc", "abc_imgur", "imgur", "youtube_"])
def test_invalid_key_names(key: str) -> None:
    assert Media.validate_key_name(key) is False


def test_key_name() -> None:
    m = Media(
        id="youtube_abc", media_type_enum=MediaType.YOUTUBE_VIDEO, foreign_key="abc"
    )
    assert m.key_name == "youtube_abc"
    assert m.slug_name == "youtube"
    assert m.foreign_key == "abc"


def test_media_type_validation() -> None:
    with pytest.raises(datastore_errors.BadValueError):
        Media(
            id="youtube_abc",
            media_type_enum=1337,
            foreign_key="abc",
        )


def test_media_tag_validation() -> None:
    with pytest.raises(datastore_errors.BadValueError):
        Media(
            id="youtube_abc",
            media_type_enum=MediaType.YOUTUBE_VIDEO,
            foreign_key="abc",
            media_tag_enum=[1337],
        )


SMUGMUG_PHOTO_DETAILS = json.dumps(
    {
        "title": "",
        "caption": "A robot",
        "web_uri": "https://nefirst.smugmug.com/2026-FIRST-AGE/2026-CMP-BAE/i-xxrbgK6",
        "image_url": "https://photos.smugmug.com/L/x-L.jpg",
        "image_url_med": "https://photos.smugmug.com/M/x-M.jpg",
        "image_url_sm": "https://photos.smugmug.com/S/x-S.jpg",
    }
)

SMUGMUG_ALBUM_DETAILS = json.dumps(
    {
        "title": "2026 FIRST Championship - BAE Systems",
        "web_uri": "https://nefirst.smugmug.com/2026-FIRST-AGE/2026-CMP-BAE",
        "image_count": 81,
        "cover_url": "https://photos.smugmug.com/L/cover-L.png",
        "cover_url_med": "https://photos.smugmug.com/M/cover-M.png",
        "cover_url_sm": "https://photos.smugmug.com/S/cover-S.png",
    }
)


def test_smugmug_photo_urls() -> None:
    m = Media(
        id="smugmug-photo_xxrbgK6",
        media_type_enum=MediaType.SMUGMUG_PHOTO,
        foreign_key="xxrbgK6",
        details_json=SMUGMUG_PHOTO_DETAILS,
    )
    assert m.key_name == "smugmug-photo_xxrbgK6"
    assert m.slug_name == "smugmug-photo"
    assert Media.validate_key_name(m.key_name) is True
    assert (
        m.view_image_url
        == "https://nefirst.smugmug.com/2026-FIRST-AGE/2026-CMP-BAE/i-xxrbgK6"
    )
    assert m.image_direct_url == "https://photos.smugmug.com/L/x-L.jpg"
    assert m.image_direct_url_med == "https://photos.smugmug.com/M/x-M.jpg"
    assert m.image_direct_url_sm == "https://photos.smugmug.com/S/x-S.jpg"


def test_smugmug_album_urls() -> None:
    m = Media(
        id="smugmug-album_4RWMLM",
        media_type_enum=MediaType.SMUGMUG_ALBUM,
        foreign_key="4RWMLM",
        details_json=SMUGMUG_ALBUM_DETAILS,
    )
    assert m.key_name == "smugmug-album_4RWMLM"
    assert m.slug_name == "smugmug-album"
    assert Media.validate_key_name(m.key_name) is True
    assert m.view_image_url == "https://nefirst.smugmug.com/2026-FIRST-AGE/2026-CMP-BAE"
    # An album has no single image, so its direct URLs are the album cover
    assert m.image_direct_url == "https://photos.smugmug.com/L/cover-L.png"
    assert m.image_direct_url_med == "https://photos.smugmug.com/M/cover-M.png"
    assert m.image_direct_url_sm == "https://photos.smugmug.com/S/cover-S.png"


@pytest.mark.parametrize(
    "media_type,is_image",
    [(MediaType.SMUGMUG_PHOTO, True), (MediaType.SMUGMUG_ALBUM, False)],
)
def test_smugmug_is_image(media_type: MediaType, is_image: bool) -> None:
    m = Media(id="smugmug_abc", media_type_enum=media_type, foreign_key="abc")
    assert m.is_image is is_image


def test_media_details_uses_orjson(monkeypatch: pytest.MonkeyPatch) -> None:
    data = {"author": "frc254", "views": 100}
    m = Media(
        id="media_123",
        media_type_enum=MediaType.CD_PHOTO_THREAD,
        foreign_key="123",
        details_json=json.dumps(data),
    )
    loads_called = False
    real_loads = orjson.loads

    def mock_loads(val: Any) -> Any:
        nonlocal loads_called
        loads_called = True
        return real_loads(val)

    monkeypatch.setattr("backend.common.models.media.orjson.loads", mock_loads)
    assert m.details == data
    assert loads_called is True
    loads_called = False
    assert m.details == data
    assert loads_called is False


def test_media_private_details_uses_orjson(monkeypatch: pytest.MonkeyPatch) -> None:
    priv = {"deletehash": "xyz"}
    m = Media(
        id="media_456",
        media_type_enum=MediaType.IMGUR,
        foreign_key="456",
        private_details_json=json.dumps(priv),
    )
    loads_called = False
    real_loads = orjson.loads

    def mock_loads(val: Any) -> Any:
        nonlocal loads_called
        loads_called = True
        return real_loads(val)

    monkeypatch.setattr("backend.common.models.media.orjson.loads", mock_loads)
    assert m.private_details == priv
    assert loads_called is True
    loads_called = False
    assert m.private_details == priv
    assert loads_called is False


def test_cdphotothread_urls() -> None:
    m = Media(
        id="cdphotothread_41999",
        media_type_enum=MediaType.CD_PHOTO_THREAD,
        foreign_key="41999",
        details_json=json.dumps({"image_partial": "a88/a880fa0d_l.jpg"}),
    )
    image_url = "https://web.archive.org/web/0im_/https://www.chiefdelphi.com/media/img/a88/a880fa0d_l.jpg"
    assert m.cdphotothread_image_url == image_url
    assert m.cdphotothread_image_url_med == image_url.replace("_l", "_m")
    assert m.cdphotothread_image_url_sm == image_url.replace("_l", "_s")
    assert (
        m.cdphotothread_thread_url
        == "https://web.archive.org/web/https://www.chiefdelphi.com/media/photos/41999"
    )
    assert m.view_image_url == image_url
    assert m.image_direct_url == m.cdphotothread_image_url_med
    assert m.image_direct_url_med == m.cdphotothread_image_url_med
    assert m.image_direct_url_sm == m.cdphotothread_image_url_sm
    assert m.is_image is True


def test_imgur_urls() -> None:
    m = Media(
        id="imgur_zYqWbBh", media_type_enum=MediaType.IMGUR, foreign_key="zYqWbBh"
    )
    assert m.imgur_url == "https://imgur.com/zYqWbBh"
    assert m.imgur_direct_url == "https://i.imgur.com/zYqWbBh.jpeg"
    assert m.imgur_direct_url_med == "https://i.imgur.com/zYqWbBhm.jpg"
    assert m.imgur_direct_url_sm == "https://i.imgur.com/zYqWbBhs.jpg"
    assert m.view_image_url == m.imgur_url
    assert m.image_direct_url == m.imgur_direct_url
    assert m.image_direct_url_med == m.imgur_direct_url_med
    assert m.image_direct_url_sm == m.imgur_direct_url_sm


def test_instagram_image_urls() -> None:
    m = Media(
        id="instagram-image_BUnZiriBYre",
        media_type_enum=MediaType.INSTAGRAM_IMAGE,
        foreign_key="BUnZiriBYre",
    )
    assert m.instagram_url == "https://www.instagram.com/p/BUnZiriBYre"
    assert m.view_image_url == m.instagram_url
    assert m.image_direct_url == m.instagram_url
    assert m.image_direct_url_med == m.instagram_url
    assert m.image_direct_url_sm == m.instagram_url


def test_grabcad_urls() -> None:
    model_image = "https://d2t1xqejof9utc.cloudfront.net/screenshots/pics/abc/card.jpg"
    m = Media(
        id="grabcad_2016-148-robowranglers-1",
        media_type_enum=MediaType.GRABCAD,
        foreign_key="2016-148-robowranglers-1",
        details_json=json.dumps({"model_image": model_image}),
    )
    assert m.view_image_url == "https://grabcad.com/library/2016-148-robowranglers-1"
    assert m.image_direct_url == model_image.replace("card.jpg", "large.png")
    assert m.image_direct_url_med == model_image
    # The small variant replaces "large.jpg", which never appears in the
    # "card.jpg" model_image GrabCAD gives us, so it is the full-size image.
    assert m.image_direct_url_sm == model_image


def test_onshape_urls() -> None:
    model_image = "https://cad.onshape.com/api/thumbnails/d/abc/w/def/s/300x300"
    m = Media(
        id="onshape_abc/w/def",
        media_type_enum=MediaType.ONSHAPE,
        foreign_key="abc/w/def",
        details_json=json.dumps({"model_image": model_image}),
    )
    assert m.view_image_url == "https://cad.onshape.com/documents/abc/w/def"
    assert m.image_direct_url == model_image.replace("300x300", "600x340")
    assert m.image_direct_url_med == model_image
    assert m.image_direct_url_sm == model_image.replace("300x300", "300x170")


def test_non_image_urls_are_empty() -> None:
    m = Media(
        id="youtube_abc", media_type_enum=MediaType.YOUTUBE_VIDEO, foreign_key="abc"
    )
    assert m.view_image_url == ""
    assert m.image_direct_url == ""
    assert m.image_direct_url_med == ""
    assert m.image_direct_url_sm == ""
    assert m.is_image is False


def test_avatar_urls() -> None:
    m = Media(
        id="avatar_avatar_2020_frc254",
        media_type_enum=MediaType.AVATAR,
        foreign_key="avatar_2020_frc254",
        year=2020,
        references=[ndb.Key(Team, "frc254")],
        details_json=json.dumps({"base64Image": "aGVsbG8="}),
    )
    assert m.avatar_base64_image == "aGVsbG8="
    assert m.avatar_image_source == "data:image/png;base64, aGVsbG8="
    assert m.avatar_image_url == "/avatar/2020/frc254.png"


def test_link_urls() -> None:
    m = Media(
        id="youtube_abc", media_type_enum=MediaType.YOUTUBE_VIDEO, foreign_key="abc"
    )
    assert m.external_link == "abc"
    assert m.youtube_url == "https://www.youtube.com/embed/abc"
    assert m.type_name == "YouTube Video"


def test_cd_thread_view_url() -> None:
    m = Media(
        id="cd-thread_12345", media_type_enum=MediaType.CD_THREAD, foreign_key="12345"
    )
    assert m.view_image_url == "https://www.chiefdelphi.com/t/12345"


def test_social_profile_url() -> None:
    social = Media(
        id="facebook-profile_frc254",
        media_type_enum=MediaType.FACEBOOK_PROFILE,
        foreign_key="frc254",
    )
    assert social.social_profile_url == "https://www.facebook.com/frc254"

    not_social = Media(
        id="youtube_abc", media_type_enum=MediaType.YOUTUBE_VIDEO, foreign_key="abc"
    )
    assert not_social.social_profile_url == ""


def test_tag_names() -> None:
    m = Media(
        id="youtube_abc",
        media_type_enum=MediaType.YOUTUBE_VIDEO,
        foreign_key="abc",
        media_tag_enum=[MediaTag.CHAIRMANS_VIDEO],
    )
    assert m.tag_names == ["Chairman's Video"]
