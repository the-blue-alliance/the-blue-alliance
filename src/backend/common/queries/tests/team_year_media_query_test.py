from google.cloud import ndb

from backend.common.consts.media_type import MediaType
from backend.common.models.media import Media
from backend.common.models.team import Team
from backend.common.queries.media_query import TeamYearMediaQuery


def test_no_data() -> None:
    medias = TeamYearMediaQuery(team_key="frc254", year=2019).fetch()
    assert medias == []


def test_excludes_media_with_no_year() -> None:
    m = Media(
        id="youtube_abc",
        media_type_enum=MediaType.YOUTUBE_VIDEO,
        foreign_key="abc",
        references=[ndb.Key(Team, "frc254")],
        year=None,
    )
    m.put()

    medias = TeamYearMediaQuery(team_key="frc254", year=2019).fetch()
    assert medias == []


def test_excludes_media_with_wrong_year() -> None:
    m = Media(
        id="youtube_abc",
        media_type_enum=MediaType.YOUTUBE_VIDEO,
        foreign_key="abc",
        references=[ndb.Key(Team, "frc254")],
        year=2018,
    )
    m.put()

    medias = TeamYearMediaQuery(team_key="frc254", year=2019).fetch()
    assert medias == []


def test_excludes_media_with_no_team() -> None:
    m = Media(
        id="youtube_abc",
        media_type_enum=MediaType.YOUTUBE_VIDEO,
        foreign_key="abc",
        year=2019,
    )
    m.put()

    medias = TeamYearMediaQuery(team_key="frc254", year=2019).fetch()
    assert medias == []


def test_excludes_media_with_wrong_team() -> None:
    m = Media(
        id="youtube_abc",
        media_type_enum=MediaType.YOUTUBE_VIDEO,
        foreign_key="abc",
        references=[ndb.Key(Team, "frc177")],
        year=2019,
    )
    m.put()

    medias = TeamYearMediaQuery(team_key="frc254", year=2019).fetch()
    assert medias == []


def test_fetch_media_with_year() -> None:
    m = Media(
        id="youtube_abc",
        media_type_enum=MediaType.YOUTUBE_VIDEO,
        foreign_key="abc",
        references=[ndb.Key(Team, "frc254")],
        year=2019,
    )
    m.put()

    medias = TeamYearMediaQuery(team_key="frc254", year=2019).fetch()
    assert medias == [m]
