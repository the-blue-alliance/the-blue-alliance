from typing import Any, cast, List, NotRequired, TypedDict

from backend.common.consts.string_enum import StrEnum
from backend.common.consts.webcast_status import WebcastStatus
from backend.common.models.webcast import Webcast
from backend.tasks_io.datafeeds.parsers.parser_base import ParserBase


class _BroadcastType(StrEnum):
    NONE = "none"
    LIVE = "live"
    UPCOMING = "upcoming"


class _StreamDataSnippet(TypedDict):
    liveBroadcastContent: _BroadcastType
    title: str


class _StreamDataLiveDetails(TypedDict):
    concurrentViewers: NotRequired[int]


class _StreamDataResponse(TypedDict):
    snippet: _StreamDataSnippet
    liveStreamingDetails: NotRequired[_StreamDataLiveDetails]


class _StreamStatusResponse(TypedDict):
    items: List[_StreamDataResponse]


class YoutubeStreamStatusParser(ParserBase[Webcast]):
    """
    See: https://developers.google.com/youtube/v3/docs/videos/list
    """

    def __init__(self, webcast: Webcast) -> None:
        super().__init__()
        self.webcast = webcast

    def parse(self, response: Any) -> Webcast:
        response_data = cast(_StreamStatusResponse, response)

        if not response_data["items"]:
            self.webcast["status"] = WebcastStatus.OFFLINE
            return self.webcast

        stream_data = response_data["items"][0]
        self.webcast["status"] = (
            WebcastStatus.ONLINE
            if stream_data["snippet"]["liveBroadcastContent"] == _BroadcastType.LIVE
            else WebcastStatus.OFFLINE
        )
        self.webcast["stream_title"] = stream_data["snippet"]["title"]

        if "liveStreamingDetails" in stream_data and (
            viewer_count := stream_data["liveStreamingDetails"].get("concurrentViewers")
        ):
            self.webcast["viewer_count"] = int(viewer_count)

        return self.webcast
