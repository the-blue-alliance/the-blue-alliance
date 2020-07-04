from backend.common.consts.media_type import MediaType, SLUG_NAMES
from backend.common.helpers.media_helper import MediaHelper


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


def test_get_socials(test_data_importer) -> None:
    year_medias = test_data_importer.parse_media_list(
        __file__, "data/frc148_media_2019.json"
    )
    social_medias = test_data_importer.parse_media_list(
        __file__, "data/frc148_social_media.json"
    )
    socials = MediaHelper.get_socials(year_medias + social_medias)
    assert socials == social_medias
