import json

from google.appengine.ext import ndb
from pyre_extensions import none_throws

from backend.common.consts.api_version import ApiMajorVersion
from backend.common.consts.media_type import MediaType
from backend.common.models.media import Media
from backend.common.queries.dict_converters.media_converter import MediaConverter


def test_mediaConverter_v3_social_media_urls(ndb_context) -> None:
    media = Media(
        id="facebook-profile_team4element",
        media_type_enum=MediaType.FACEBOOK_PROFILE,
        foreign_key="team4element",
        references=[ndb.Key("Team", "frc4")],
    )
    result = MediaConverter.mediaConverter_v3(media)
    assert result["view_url"] == "https://www.facebook.com/team4element"
    assert result["direct_url"] == "https://www.facebook.com/team4element"


def test_mediaConverter_v3_github_profile_url(ndb_context) -> None:
    media = Media(
        id="github-profile_tba",
        media_type_enum=MediaType.GITHUB_PROFILE,
        foreign_key="the-blue-alliance",
        references=[ndb.Key("Team", "frc4")],
    )
    result = MediaConverter.mediaConverter_v3(media)
    assert result["view_url"] == "https://github.com/the-blue-alliance"
    assert result["direct_url"] == "https://github.com/the-blue-alliance"


def test_mediaConverter_v3_youtube_channel_url(ndb_context) -> None:
    media = Media(
        id="youtube-channel_frcteam4element",
        media_type_enum=MediaType.YOUTUBE_CHANNEL,
        foreign_key="@frcteam4element",
        references=[ndb.Key("Team", "frc4")],
    )
    result = MediaConverter.mediaConverter_v3(media)
    assert result["view_url"] == "https://www.youtube.com/@frcteam4element"
    assert result["direct_url"] == "https://www.youtube.com/@frcteam4element"


def test_mediaConverter_v3_youtube_video(ndb_context) -> None:
    media = Media(
        id="youtube_abc123",
        media_type_enum=MediaType.YOUTUBE_VIDEO,
        foreign_key="abc123",
        references=[ndb.Key("Team", "frc4")],
    )
    result = MediaConverter.mediaConverter_v3(media)
    assert result["view_url"] == "https://youtu.be/abc123"
    assert result["direct_url"] == "https://img.youtube.com/vi/abc123/hqdefault.jpg"


def test_mediaConverter_v3_instagram_profile_url(ndb_context) -> None:
    media = Media(
        id="instagram-profile_frc4",
        media_type_enum=MediaType.INSTAGRAM_PROFILE,
        foreign_key="frc4",
        references=[ndb.Key("Team", "frc4")],
    )
    result = MediaConverter.mediaConverter_v3(media)
    assert result["view_url"] == "https://www.instagram.com/frc4"
    assert result["direct_url"] == "https://www.instagram.com/frc4"


def test_mediaConverter_v3_twitter_profile_url(ndb_context) -> None:
    media = Media(
        id="twitter-profile_frc4",
        media_type_enum=MediaType.TWITTER_PROFILE,
        foreign_key="frc4",
        references=[ndb.Key("Team", "frc4")],
    )
    result = MediaConverter.mediaConverter_v3(media)
    assert result["view_url"] == "https://twitter.com/frc4"
    assert result["direct_url"] == "https://twitter.com/frc4"


def test_mediaConverter_v3_smugmug_photo(ndb_context) -> None:
    media = Media(
        id="smugmug-photo_xxrbgK6",
        media_type_enum=MediaType.SMUGMUG_PHOTO,
        foreign_key="xxrbgK6",
        details_json=json.dumps(
            {
                "title": "",
                "caption": "A robot",
                "web_uri": "https://nefirst.smugmug.com/2026-FIRST-AGE/2026-CMP-BAE/i-xxrbgK6",
                "image_url": "https://photos.smugmug.com/L/x-L.jpg",
                "image_url_med": "https://photos.smugmug.com/M/x-M.jpg",
                "image_url_sm": "https://photos.smugmug.com/S/x-S.jpg",
            }
        ),
        references=[ndb.Key("Team", "frc4")],
    )
    result = MediaConverter.mediaConverter_v3(media)
    assert result["type"] == "smugmug-photo"
    assert (
        result["view_url"]
        == "https://nefirst.smugmug.com/2026-FIRST-AGE/2026-CMP-BAE/i-xxrbgK6"
    )
    assert result["direct_url"] == "https://photos.smugmug.com/L/x-L.jpg"


def _cad_media(media_type: MediaType, model_created: str) -> Media:
    return Media(
        id="onshape_abc123",
        media_type_enum=media_type,
        foreign_key="abc123",
        details_json=json.dumps(
            {
                "model_name": "Robot",
                "model_description": "",
                "model_image": "https://cad.onshape.com/api/thumbnails/d/abc123/s/300x300",
                "model_created": model_created,
            }
        ),
        references=[ndb.Key("Team", "frc4")],
    )


def test_mediaConverter_v3_onshape_colonless_offset_normalized(ndb_context) -> None:
    media = _cad_media(MediaType.ONSHAPE, "2019-09-25T00:12:49.122+0000")
    result = MediaConverter.mediaConverter_v3(media)
    assert result["details"]["model_created"] == "2019-09-25T00:12:49.122+00:00"


def test_mediaConverter_v3_onshape_valid_offset_unchanged(ndb_context) -> None:
    media = _cad_media(MediaType.ONSHAPE, "2019-09-25T00:12:49.122+00:00")
    result = MediaConverter.mediaConverter_v3(media)
    assert result["details"]["model_created"] == "2019-09-25T00:12:49.122+00:00"


def test_mediaConverter_v3_grabcad_zulu_unchanged(ndb_context) -> None:
    media = _cad_media(MediaType.GRABCAD, "2016-09-19T11:52:23Z")
    result = MediaConverter.mediaConverter_v3(media)
    assert result["details"]["model_created"] == "2016-09-19T11:52:23Z"


def test_mediaConverter_v3_onshape_unparseable_model_created_is_none(
    ndb_context,
) -> None:
    media = _cad_media(MediaType.ONSHAPE, "")
    result = MediaConverter.mediaConverter_v3(media)
    assert result["details"]["model_created"] is None


def test_mediaConverter_v3_does_not_mutate_model_details(ndb_context) -> None:
    media = _cad_media(MediaType.ONSHAPE, "2019-09-25T00:12:49.122+0000")
    MediaConverter.mediaConverter_v3(media)
    details = none_throws(media.details)
    assert details["model_created"] == "2019-09-25T00:12:49.122+0000"


def test_mediaConverter_v3_smugmug_album(ndb_context) -> None:
    media = Media(
        id="smugmug-album_4RWMLM",
        media_type_enum=MediaType.SMUGMUG_ALBUM,
        foreign_key="4RWMLM",
        details_json=json.dumps(
            {
                "title": "2026 FIRST Championship - BAE Systems",
                "web_uri": "https://nefirst.smugmug.com/2026-FIRST-AGE/2026-CMP-BAE",
                "image_count": 81,
                "cover_url": "https://photos.smugmug.com/L/cover-L.png",
                "cover_url_med": "https://photos.smugmug.com/M/cover-M.png",
                "cover_url_sm": "https://photos.smugmug.com/S/cover-S.png",
            }
        ),
        references=[ndb.Key("Event", "2026necmp")],
    )
    result = MediaConverter.mediaConverter_v3(media)
    assert result["type"] == "smugmug-album"
    assert (
        result["view_url"] == "https://nefirst.smugmug.com/2026-FIRST-AGE/2026-CMP-BAE"
    )
    assert result["direct_url"] == "https://photos.smugmug.com/L/cover-L.png"
    assert result["team_keys"] == []


def test_mediaConverter_v3_instagram_image(ndb_context) -> None:
    media = Media(
        id="instagram-image_BUnZiriBYre",
        media_type_enum=MediaType.INSTAGRAM_IMAGE,
        foreign_key="BUnZiriBYre",
        references=[ndb.Key("Team", "frc195")],
    )
    result = MediaConverter.mediaConverter_v3(media)
    assert result["type"] == "instagram-image"
    assert result["view_url"] == "https://www.instagram.com/p/BUnZiriBYre"
    assert result["direct_url"] == "https://www.instagram.com/p/BUnZiriBYre"


def test_mediaConverter_v3_onshape_non_string_model_created_is_none(
    ndb_context,
) -> None:
    media = Media(
        id="onshape_abc123",
        media_type_enum=MediaType.ONSHAPE,
        foreign_key="abc123",
        details_json=json.dumps(
            {
                "model_name": "Robot",
                "model_description": "",
                "model_image": "https://cad.onshape.com/api/thumbnails/d/abc123/s/300x300",
                "model_created": 1569370369,
            }
        ),
        references=[ndb.Key("Team", "frc4")],
    )
    result = MediaConverter.mediaConverter_v3(media)
    assert result["details"]["model_created"] is None


def test_convert_list(ndb_context) -> None:
    media = Media(
        id="youtube_abc",
        media_type_enum=MediaType.YOUTUBE_VIDEO,
        foreign_key="abc",
        references=[ndb.Key("Team", "frc4")],
    )
    converted = MediaConverter([media]).convert(ApiMajorVersion.API_V3)
    assert converted == [MediaConverter.mediaConverter_v3(media)]


def test_dictToModel_v3_with_team(ndb_context) -> None:
    media = MediaConverter.dictToModel_v3(
        {
            "type": "youtube",
            "foreign_key": "abc",
            "details": {"foo": "bar"},
            "preferred": True,
        },
        2020,
        "frc254",
    )

    assert media.key.id() == Media.render_key_name(MediaType.YOUTUBE_VIDEO, "abc")
    assert media.media_type_enum == MediaType.YOUTUBE_VIDEO
    assert media.foreign_key == "abc"
    assert media.details == {"foo": "bar"}
    assert media.references == [ndb.Key("Team", "frc254")]
    assert media.preferred_references == [ndb.Key("Team", "frc254")]
    assert media.year == 2020


def test_dictToModel_v3_without_team(ndb_context) -> None:
    media = MediaConverter.dictToModel_v3(
        {
            "type": "imgur",
            "foreign_key": "xyz",
            "details": {},
            "preferred": True,
        },
        None,
        None,
    )

    assert media.media_type_enum == MediaType.IMGUR
    assert media.references == []
    assert media.preferred_references == []
    assert media.year is None
