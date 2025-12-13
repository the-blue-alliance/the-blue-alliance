from typing import Literal, Optional

from pyre_extensions import JSON

from backend.common.consts.webcast_status import WebcastStatus
from backend.common.consts.webcast_type import WebcastType
from backend.common.models.webcast import Webcast
from backend.tasks_io.datafeeds.parsers.youtube.youtube_stream_stauts_parser import (
    YoutubeStreamStatusParser,
)


def get_api_response(
    status: Literal["live", "none", "upcoming"], viewers: Optional[int]
):
    live_details = {
        "actualStartTime": "2025-03-29T14:33:11Z",
        "actualEndTime": "2025-03-29T22:04:00Z",
        "scheduledStartTime": "2025-03-29T14:30:00Z",
    }
    if status == "live":
        live_details["concurrentViewers"] = f"{viewers}"

    return {
        "items": [
            {
                "snippet": {
                    "liveBroadcastContent": status,
                    "title": "A Stream",
                },
                "liveStreamingDetails": live_details,
            }
        ]
    }


def test_parse_no_stream() -> None:
    w = Webcast(type=WebcastType.YOUTUBE, channel="abc123")
    resp: JSON = {"items": []}
    parsed = YoutubeStreamStatusParser(w).parse(resp)

    assert parsed == Webcast(
        type=WebcastType.YOUTUBE,
        channel="abc123",
        status=WebcastStatus.OFFLINE,
    )


def test_parse_offline() -> None:
    w = Webcast(type=WebcastType.YOUTUBE, channel="abc123")
    resp: JSON = get_api_response(status="none", viewers=None)
    parsed = YoutubeStreamStatusParser(w).parse(resp)

    assert parsed == Webcast(
        type=WebcastType.YOUTUBE,
        channel="abc123",
        status=WebcastStatus.OFFLINE,
        stream_title="A Stream",
    )


def test_parse_live() -> None:
    w = Webcast(type=WebcastType.YOUTUBE, channel="abc123")
    resp: JSON = get_api_response(status="live", viewers=100)
    parsed = YoutubeStreamStatusParser(w).parse(resp)

    assert parsed == Webcast(
        type=WebcastType.YOUTUBE,
        channel="abc123",
        status=WebcastStatus.ONLINE,
        stream_title="A Stream",
        viewer_count=100,
    )
