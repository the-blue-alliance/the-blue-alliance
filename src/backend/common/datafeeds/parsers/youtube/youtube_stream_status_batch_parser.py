from typing import Any, cast, Dict, List, NotRequired, TypedDict

from backend.common.consts.string_enum import StrEnum
from backend.common.consts.webcast_status import WebcastStatus
from backend.common.datafeeds.parsers.parser_base import ParserBase
from backend.common.models.webcast import WebcastOnlineStatus


class _BroadcastType(StrEnum):
    NONE = "none"
    LIVE = "live"
    UPCOMING = "upcoming"


class _StreamDataSnippet(TypedDict):
    liveBroadcastContent: _BroadcastType
    title: str


class _StreamDataLiveDetails(TypedDict):
    concurrentViewers: NotRequired[int]
    scheduledStartTime: NotRequired[str]


class _StreamDataResponseWithId(TypedDict):
    id: str
    snippet: _StreamDataSnippet
    liveStreamingDetails: NotRequired[_StreamDataLiveDetails]


class _StreamStatusResponseBatch(TypedDict):
    items: List[_StreamDataResponseWithId]


class YoutubeStreamStatusBatchParser(ParserBase[Any, Dict[str, WebcastOnlineStatus]]):
    """
    Parses batch YouTube API response and returns status data for multiple videos.
    Returns a dictionary mapping video IDs to their online status, without mutating models.
    """

    def __init__(self, video_ids: List[str]) -> None:
        super().__init__()
        self.video_ids = video_ids

    def parse(self, response: Any) -> Dict[str, WebcastOnlineStatus]:
        response_data = cast(_StreamStatusResponseBatch, response)
        result: Dict[str, WebcastOnlineStatus] = {}

        if not response_data.get("items"):
            for video_id in self.video_ids:
                result[video_id] = WebcastOnlineStatus(status=WebcastStatus.OFFLINE)
            return result

        for stream_data in response_data["items"]:
            video_id = stream_data.get("id", "")
            if not video_id:
                continue

            status_data = self._extract_status(stream_data)
            result[video_id] = status_data

        for video_id in self.video_ids:
            if video_id not in result:
                result[video_id] = WebcastOnlineStatus(status=WebcastStatus.OFFLINE)

        return result

    def _extract_status(
        self, stream_data: _StreamDataResponseWithId
    ) -> WebcastOnlineStatus:
        status_info: WebcastOnlineStatus = {}

        snippet = stream_data.get("snippet")
        if not snippet:
            status_info["status"] = WebcastStatus.OFFLINE
            return status_info

        live_broadcast_content: str = snippet.get(
            "liveBroadcastContent", _BroadcastType.NONE
        )
        status_info["status"] = (
            WebcastStatus.ONLINE
            if live_broadcast_content == _BroadcastType.LIVE
            else WebcastStatus.OFFLINE
        )
        status_info["stream_title"] = snippet.get("title")

        live_details = stream_data.get("liveStreamingDetails")
        if live_details:
            if "concurrentViewers" in live_details:
                status_info["viewer_count"] = int(live_details["concurrentViewers"])
            if "scheduledStartTime" in live_details:
                status_info["scheduled_start_time_utc"] = live_details[
                    "scheduledStartTime"
                ]

        return status_info
