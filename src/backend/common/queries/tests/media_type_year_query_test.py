from backend.common.consts.media_type import MediaType
from backend.common.models.media import Media
from backend.common.queries.media_query import MediaTypeYearQuery


def test_no_data() -> None:
    assert (
        MediaTypeYearQuery(media_type=MediaType.YOUTUBE_VIDEO, year=2020).fetch() == []
    )


def test_fetch_medias() -> None:
    video = Media(
        id=Media.render_key_name(MediaType.YOUTUBE_VIDEO, "abc"),
        foreign_key="abc",
        media_type_enum=MediaType.YOUTUBE_VIDEO,
        year=2020,
    )
    video.put()
    Media(
        id=Media.render_key_name(MediaType.YOUTUBE_VIDEO, "def"),
        foreign_key="def",
        media_type_enum=MediaType.YOUTUBE_VIDEO,
        year=2019,
    ).put()
    Media(
        id=Media.render_key_name(MediaType.IMGUR, "ghi"),
        foreign_key="ghi",
        media_type_enum=MediaType.IMGUR,
        year=2020,
    ).put()

    assert MediaTypeYearQuery(
        media_type=MediaType.YOUTUBE_VIDEO, year=2020
    ).fetch() == [video]
