"""Parser for YouTube video details API response.

Follows YouTube Data API v3 schema:
https://developers.google.com/youtube/v3/docs/videos/list
"""

from typing import Any, cast, List, NotRequired, Optional, TypedDict

from backend.common.datafeeds.parsers.parser_base import ParserBase


class _VideoSnippet(TypedDict):
    """Video snippet information."""

    title: str
    description: NotRequired[str]
    channelId: NotRequired[str]
    channelTitle: NotRequired[str]
    publishedAt: NotRequired[str]


class _LiveStreamingDetails(TypedDict):
    """Live streaming details for a video."""

    actualStartTime: NotRequired[str]
    scheduledStartTime: NotRequired[str]
    actualEndTime: NotRequired[str]
    concurrentViewers: NotRequired[str]


class _VideoItem(TypedDict):
    """A single item from the videos list response."""

    id: str
    snippet: NotRequired[_VideoSnippet]
    liveStreamingDetails: NotRequired[_LiveStreamingDetails]


class _VideosListResponse(TypedDict):
    """Response from videos.list API call."""

    items: List[_VideoItem]
    nextPageToken: NotRequired[str]


class ParsedVideoDetails(TypedDict):
    """Parsed video details - what we return to callers."""

    video_id: str
    title: str
    scheduled_start_time: NotRequired[Optional[str]]
    actual_start_time: NotRequired[Optional[str]]
    concurrent_viewers: NotRequired[Optional[int]]


class YoutubeVideoDetailsParser(ParserBase[Any, Optional[ParsedVideoDetails]]):
    """
    Parses YouTube video details from the videos.list API response.

    Returns parsed details for the first (and typically only) video in the response.
    Returns None if no items are in the response.
    """

    def parse(self, response: Any) -> Optional[ParsedVideoDetails]:
        response_data = cast(_VideosListResponse, response)

        items = response_data.get("items", [])
        if not items:
            return None

        item = items[0]
        video_id = item.get("id", "")
        if not video_id:
            return None

        result: ParsedVideoDetails = {"video_id": video_id, "title": ""}

        snippet = item.get("snippet")
        if snippet:
            result["title"] = snippet.get("title", "")

        live_details = item.get("liveStreamingDetails")
        if live_details:
            scheduled_start = live_details.get("scheduledStartTime")
            if scheduled_start:
                result["scheduled_start_time"] = scheduled_start[:10]

            actual_start = live_details.get("actualStartTime")
            if actual_start:
                result["actual_start_time"] = actual_start[:10]

            viewers_str = live_details.get("concurrentViewers")
            if viewers_str:
                try:
                    result["concurrent_viewers"] = int(viewers_str)
                except (ValueError, TypeError):
                    pass

        return result
