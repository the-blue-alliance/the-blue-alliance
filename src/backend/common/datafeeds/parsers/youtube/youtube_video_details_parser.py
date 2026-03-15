"""Parser for YouTube video details API response.

Follows YouTube Data API v3 schema:
https://developers.google.com/youtube/v3/docs/videos/list
"""

from typing import Any, cast, Dict, List, NotRequired, Optional, TypedDict

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
    channel_id: NotRequired[Optional[str]]
    description: NotRequired[str]
    scheduled_start_time: NotRequired[Optional[str]]
    actual_start_time: NotRequired[Optional[str]]
    concurrent_viewers: NotRequired[Optional[int]]


def _parse_video_item(item: _VideoItem) -> Optional[ParsedVideoDetails]:
    """Parse a single video API item into ParsedVideoDetails, or None if invalid."""
    video_id = item.get("id", "")
    if not video_id:
        return None

    result: ParsedVideoDetails = {"video_id": video_id, "title": ""}

    snippet = item.get("snippet")
    if snippet:
        result["title"] = snippet.get("title", "")
        channel_id = snippet.get("channelId")
        if channel_id:
            result["channel_id"] = channel_id
        description = snippet.get("description")
        if description:
            result["description"] = description

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


class YoutubeVideoDetailsParser(ParserBase[Any, Dict[str, ParsedVideoDetails]]):
    """
    Parses YouTube video details from the videos.list API response.

    Returns a dict mapping video_id -> ParsedVideoDetails for every video
    present in the response. Video IDs absent from the response are not
    included in the result (absence == deleted/invalid).
    """

    def parse(self, response: Any) -> Dict[str, ParsedVideoDetails]:
        response_data = cast(_VideosListResponse, response)

        result: Dict[str, ParsedVideoDetails] = {}
        for item in response_data.get("items", []):
            parsed = _parse_video_item(item)
            if parsed is not None:
                result[parsed["video_id"]] = parsed

        return result
