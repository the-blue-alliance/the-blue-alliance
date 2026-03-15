"""Parser for batched YouTube liveStreamingDetails video response.

Follows YouTube Data API v3 schema:
https://developers.google.com/youtube/v3/docs/videos/list
"""

from typing import Any, cast, Dict, List, NotRequired, Optional, TypedDict

from backend.common.datafeeds.parsers.parser_base import ParserBase


class _VideoLiveDetails(TypedDict):
    scheduledStartTime: NotRequired[str]


class _VideoLiveDetailsItem(TypedDict):
    id: str
    liveStreamingDetails: NotRequired[_VideoLiveDetails]


class _VideosLiveDetailsResponse(TypedDict):
    items: List[_VideoLiveDetailsItem]


class YoutubeVideoLiveDetailsBatchParser(ParserBase[Any, Dict[str, Optional[str]]]):
    def __init__(self, video_ids: List[str]) -> None:
        super().__init__()
        self.video_ids = video_ids

    def parse(self, response: Any) -> Dict[str, Optional[str]]:
        response_data = cast(_VideosLiveDetailsResponse, response)

        # Initialize all video IDs as None (not found in YouTube API)
        result: Dict[str, Optional[str]] = {
            video_id: None for video_id in self.video_ids
        }
        for item in response_data.get("items", []):
            video_id = item.get("id", "")
            if not video_id:
                continue
            live_details = item.get("liveStreamingDetails") or {}
            scheduled_time = live_details.get("scheduledStartTime", "")
            # Truncate to YYYY-MM-DD format if a valid timestamp is present
            result[video_id] = scheduled_time[:10] if len(scheduled_time) >= 10 else ""

        return result
