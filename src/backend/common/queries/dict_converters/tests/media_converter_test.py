import json

from google.appengine.ext import ndb

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
    assert result["direct_url"] == ""
    assert result["team_keys"] == []
