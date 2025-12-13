import pytest

from backend.common.consts.webcast_status import WebcastStatus
from backend.common.consts.webcast_type import WebcastType
from backend.common.helpers.special_webcast_helper import SpecialWebcastHelper
from backend.common.memcache_models.webcast_online_status_memcache import (
    WebcastOnlineStatusMemcache,
)
from backend.common.sitevars.gameday_special_webcasts import (
    ContentType as TGamedaySpecialWebcastsContent,
    GamedaySpecialWebcasts,
    WebcastType as TSpecialWebcast,
)


@pytest.fixture(autouse=True)
def auto_add_ndb_stub(ndb_stub) -> None:
    pass


def test_special_webcasts_with_live_info() -> None:
    GamedaySpecialWebcasts.put(
        TGamedaySpecialWebcastsContent(
            default_chat="",
            aliases={},
            webcasts=[
                TSpecialWebcast(
                    type=WebcastType.YOUTUBE,
                    key_name="special",
                    channel="abc123",
                    name="Special Webcast",
                )
            ],
        )
    )

    w = TSpecialWebcast(
        name="Special Webcast",
        key_name="special",
        type=WebcastType.YOUTUBE,
        channel="abc123",
        status=WebcastStatus.ONLINE,
        stream_title="Test stream",
        viewer_count=100,
    )
    WebcastOnlineStatusMemcache(w).put(w)

    special_webcasts = SpecialWebcastHelper.get_special_webcasts_with_online_status()

    assert len(special_webcasts) == 1
    assert special_webcasts[0] == TSpecialWebcast(
        name="Special Webcast",
        key_name="special",
        type=WebcastType.YOUTUBE,
        channel="abc123",
        status=WebcastStatus.ONLINE,
        stream_title="Test stream",
        viewer_count=100,
    )


def test_special_webcasts_without_live_info() -> None:
    GamedaySpecialWebcasts.put(
        TGamedaySpecialWebcastsContent(
            default_chat="",
            aliases={},
            webcasts=[
                TSpecialWebcast(
                    type=WebcastType.YOUTUBE,
                    key_name="special",
                    channel="abc123",
                    name="Special Webcast",
                )
            ],
        )
    )

    special_webcasts = SpecialWebcastHelper.get_special_webcasts_with_online_status()

    assert len(special_webcasts) == 1
    assert special_webcasts[0] == TSpecialWebcast(
        name="Special Webcast",
        key_name="special",
        type=WebcastType.YOUTUBE,
        channel="abc123",
    )
