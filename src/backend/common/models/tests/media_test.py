import json

import pytest
from google.appengine.api import datastore_errors

from backend.common.consts.media_type import MediaType
from backend.common.models.media import Media


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
