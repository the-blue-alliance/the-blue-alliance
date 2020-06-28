from google.cloud import ndb

from backend.common.consts.media_type import MediaType
from backend.common.models.event import Event
from backend.common.models.media import Media
from backend.common.queries.media_query import EventMediasQuery


def test_no_data() -> None:
    medias = EventMediasQuery(event_key="2010ct").fetch()
    assert medias == []


def test_excludes_media_with_no_references() -> None:
    m = Media(
        id="youtube_abc",
        media_type_enum=MediaType.YOUTUBE_VIDEO,
        foreign_key="abc",
        year=2010,
    )
    m.put()

    medias = EventMediasQuery(event_key="2010ct").fetch()
    assert medias == []


def test_excludes_media_with_wrong_event() -> None:
    m = Media(
        id="youtube_abc",
        media_type_enum=MediaType.YOUTUBE_VIDEO,
        foreign_key="abc",
        references=[ndb.Key(Event, "2010nyc")],
        year=2010,
    )
    m.put()

    medias = EventMediasQuery(event_key="2010ct").fetch()
    assert medias == []


def test_fetch_medias() -> None:
    m = Media(
        id="youtube_abc",
        media_type_enum=MediaType.YOUTUBE_VIDEO,
        foreign_key="abc",
        references=[ndb.Key(Event, "2010ct")],
        year=2010,
    )
    m.put()

    medias = EventMediasQuery(event_key="2010ct").fetch()
    assert medias == [m]
