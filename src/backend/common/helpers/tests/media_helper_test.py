from google.appengine.ext import ndb

from backend.common.consts.media_type import MediaType, SLUG_NAMES
from backend.common.helpers.media_helper import MediaHelper
from backend.common.models.media import Media
from backend.common.models.team import Team


def test_organize_media(test_data_importer) -> None:
    medias = test_data_importer.parse_media_list(
        __file__, "data/frc148_media_2019.json", 2019
    )
    organized_medias = MediaHelper.group_by_slugname(medias)

    assert len(organized_medias[SLUG_NAMES[MediaType.AVATAR]]) == 1
    assert len(organized_medias[SLUG_NAMES[MediaType.YOUTUBE_VIDEO]]) == 2
    assert len(organized_medias[SLUG_NAMES[MediaType.IMGUR]]) == 1


def test_get_avatar(test_data_importer) -> None:
    medias = test_data_importer.parse_media_list(
        __file__, "data/frc148_media_2019.json", 2019
    )
    avatar = MediaHelper.get_avatar(medias)
    assert avatar is not None
    assert avatar.key_name == "avatar_avatar_2019_frc148"


def test_get_avatar_not_found(test_data_importer) -> None:
    medias = test_data_importer.parse_media_list(
        __file__, "data/frc148_social_media.json"
    )
    avatar = MediaHelper.get_avatar(medias)
    assert avatar is None


def test_get_images(test_data_importer) -> None:
    medias = test_data_importer.parse_media_list(
        __file__, "data/frc148_media_2019.json"
    )
    images = MediaHelper.get_images(medias)
    assert len(images) == 1


def test_get_preferred_or_fallback_images_prefers_preferred() -> None:
    team_key = ndb.Key(Team, "frc148")
    fallback = Media(
        id="imgur_fallback",
        media_type_enum=MediaType.IMGUR,
        foreign_key="fallback",
        references=[team_key],
        year=2025,
    )
    preferred = Media(
        id="imgur_preferred",
        media_type_enum=MediaType.IMGUR,
        foreign_key="preferred",
        references=[team_key],
        preferred_references=[team_key],
        year=2025,
    )

    images = MediaHelper.get_preferred_or_fallback_images(
        [fallback, preferred], team_key
    )

    assert images == [preferred]


def test_get_preferred_or_fallback_images_uses_fallback() -> None:
    team_key = ndb.Key(Team, "frc148")
    fallback = Media(
        id="imgur_fallback",
        media_type_enum=MediaType.IMGUR,
        foreign_key="fallback",
        references=[team_key],
        year=2025,
    )

    images = MediaHelper.get_preferred_or_fallback_images([fallback], team_key)

    assert images == [fallback]


def test_get_preferred_or_fallback_images_without_media() -> None:
    team_key = ndb.Key(Team, "frc148")

    images = MediaHelper.get_preferred_or_fallback_images([], team_key)

    assert images == []


def test_get_socials(test_data_importer) -> None:
    year_medias = test_data_importer.parse_media_list(
        __file__, "data/frc148_media_2019.json"
    )
    social_medias = test_data_importer.parse_media_list(
        __file__, "data/frc148_social_media.json"
    )
    socials = MediaHelper.get_socials(year_medias + social_medias)
    assert socials == social_medias
