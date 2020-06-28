import pytest
from google.cloud import ndb

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
    with pytest.raises(ndb.exceptions.BadValueError):
        Media(
            id="youtube_abc", media_type_enum=1337, foreign_key="abc",
        )


def test_media_tag_validation() -> None:
    with pytest.raises(ndb.exceptions.BadValueError):
        Media(
            id="youtube_abc",
            media_type_enum=MediaType.YOUTUBE_VIDEO,
            foreign_key="abc",
            media_tag_enum=[1337],
        )
