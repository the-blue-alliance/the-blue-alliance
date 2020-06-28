from google.cloud import ndb

from backend.common.consts.media_type import MediaType
from backend.common.models.event import Event
from backend.common.models.event_team import EventTeam
from backend.common.models.media import Media
from backend.common.models.team import Team
from backend.common.queries.media_query import EventTeamsPreferredMediasQuery


def test_no_data() -> None:
    medias = EventTeamsPreferredMediasQuery(event_key="2010ct").fetch()
    assert medias == []


def test_exclude_media_no_year() -> None:
    et = EventTeam(
        id="2010ct_frc254", event=ndb.Key(Event, "2010ct"), team=ndb.Key(Team, "frc254")
    )
    et.put()

    m = Media(
        id="youtube_abc",
        media_type_enum=MediaType.YOUTUBE_VIDEO,
        foreign_key="abc",
        preferred_references=[ndb.Key(Team, "frc254")],
        year=None,
    )
    m.put()

    medias = EventTeamsPreferredMediasQuery(event_key="2010ct").fetch()
    assert medias == []


def test_exclude_media_non_preferred() -> None:
    et = EventTeam(
        id="2010ct_frc254", event=ndb.Key(Event, "2010ct"), team=ndb.Key(Team, "frc254")
    )
    et.put()

    m = Media(
        id="youtube_abc",
        media_type_enum=MediaType.YOUTUBE_VIDEO,
        foreign_key="abc",
        references=[ndb.Key(Team, "frc254")],
        year=None,
    )
    m.put()

    medias = EventTeamsPreferredMediasQuery(event_key="2010ct").fetch()
    assert medias == []


def test_exclude_media_other_team() -> None:
    et = EventTeam(
        id="2010ct_frc254", event=ndb.Key(Event, "2010ct"), team=ndb.Key(Team, "frc254")
    )
    et.put()

    m = Media(
        id="youtube_abc",
        media_type_enum=MediaType.YOUTUBE_VIDEO,
        foreign_key="abc",
        preferred_references=[ndb.Key(Team, "frc177")],
        year=None,
    )
    m.put()

    medias = EventTeamsPreferredMediasQuery(event_key="2010ct").fetch()
    assert medias == []


def test_fetch_medias() -> None:
    et = EventTeam(
        id="2010ct_frc254", event=ndb.Key(Event, "2010ct"), team=ndb.Key(Team, "frc254")
    )
    et.put()

    m = Media(
        id="youtube_abc",
        media_type_enum=MediaType.YOUTUBE_VIDEO,
        foreign_key="abc",
        preferred_references=[ndb.Key(Team, "frc254")],
        year=2010,
    )
    m.put()

    medias = EventTeamsPreferredMediasQuery(event_key="2010ct").fetch()
    assert medias == [m]
