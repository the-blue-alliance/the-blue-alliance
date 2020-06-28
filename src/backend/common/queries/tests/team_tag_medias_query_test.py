from google.cloud import ndb

from backend.common.consts.media_tag import MediaTag
from backend.common.consts.media_type import MediaType
from backend.common.models.media import Media
from backend.common.models.team import Team
from backend.common.queries.media_query import TeamTagMediasQuery


def test_no_data() -> None:
    medias = TeamTagMediasQuery(
        team_key="frc254", media_tag=MediaTag.CHAIRMANS_VIDEO
    ).fetch()
    assert medias == []


def test_excludes_media_with_no_team() -> None:
    m = Media(
        id="youtube_abc",
        media_type_enum=MediaType.YOUTUBE_VIDEO,
        foreign_key="abc",
        year=2019,
        media_tag_enum=[MediaTag.CHAIRMANS_VIDEO],
    )
    m.put()

    medias = TeamTagMediasQuery(
        team_key="frc254", media_tag=MediaTag.CHAIRMANS_VIDEO
    ).fetch()
    assert medias == []


def test_excludes_media_with_wrong_team() -> None:
    m = Media(
        id="youtube_abc",
        media_type_enum=MediaType.YOUTUBE_VIDEO,
        foreign_key="abc",
        references=[ndb.Key(Team, "frc177")],
        year=2019,
        media_tag_enum=[MediaTag.CHAIRMANS_VIDEO],
    )
    m.put()

    medias = TeamTagMediasQuery(
        team_key="frc254", media_tag=MediaTag.CHAIRMANS_VIDEO
    ).fetch()
    assert medias == []


def test_exclude_no_tag() -> None:
    m = Media(
        id="youtube_abc",
        media_type_enum=MediaType.YOUTUBE_VIDEO,
        foreign_key="abc",
        references=[ndb.Key(Team, "frc254")],
        year=2019,
    )
    m.put()

    medias = TeamTagMediasQuery(
        team_key="frc254", media_tag=MediaTag.CHAIRMANS_VIDEO
    ).fetch()
    assert medias == []


def test_exclude_wrong_tag() -> None:
    m = Media(
        id="youtube_abc",
        media_type_enum=MediaType.YOUTUBE_VIDEO,
        foreign_key="abc",
        references=[ndb.Key(Team, "frc254")],
        year=2019,
        media_tag_enum=[MediaTag.CHAIRMANS_PRESENTATION],
    )
    m.put()

    medias = TeamTagMediasQuery(
        team_key="frc254", media_tag=MediaTag.CHAIRMANS_VIDEO
    ).fetch()
    assert medias == []


def test_fetch_medias() -> None:
    m = Media(
        id="youtube_abc",
        media_type_enum=MediaType.YOUTUBE_VIDEO,
        foreign_key="abc",
        references=[ndb.Key(Team, "frc254")],
        year=2019,
        media_tag_enum=[MediaTag.CHAIRMANS_VIDEO],
    )
    m.put()

    medias = TeamTagMediasQuery(
        team_key="frc254", media_tag=MediaTag.CHAIRMANS_VIDEO
    ).fetch()
    assert medias == [m]
