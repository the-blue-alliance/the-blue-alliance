from google.cloud import ndb

from backend.common.consts.media_type import MediaType
from backend.common.models.media import Media
from backend.common.models.team import Team
from backend.common.queries.media_query import TeamMediaQuery


def test_no_data() -> None:
    medias = TeamMediaQuery(team_key="frc254").fetch()
    assert medias == []


def test_excludes_media_with_no_team() -> None:
    m = Media(
        id="youtube_abc",
        media_type_enum=MediaType.YOUTUBE_VIDEO,
        foreign_key="abc",
        year=2019,
    )
    m.put()

    medias = TeamMediaQuery(team_key="frc254").fetch()
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

    medias = TeamMediaQuery(team_key="frc254").fetch()
    assert medias == []


def test_fetch_medias() -> None:
    m1 = Media(
        id="youtube_abc",
        media_type_enum=MediaType.YOUTUBE_VIDEO,
        foreign_key="abc",
        references=[ndb.Key(Team, "frc254")],
        year=2019,
    )
    m1.put()

    m2 = Media(
        id="youtube_abcd",
        media_type_enum=MediaType.YOUTUBE_VIDEO,
        foreign_key="abcd",
        references=[ndb.Key(Team, "frc254")],
        year=None,
    )
    m2.put()

    medias = TeamMediaQuery(team_key="frc254").fetch()
    assert medias == [m1, m2]
