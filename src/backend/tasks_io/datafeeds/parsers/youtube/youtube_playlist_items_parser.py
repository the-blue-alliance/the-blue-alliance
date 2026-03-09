"""Parser for YouTube playlist items API response.

Follows YouTube Data API v3 schema:
https://developers.google.com/youtube/v3/docs/playlistItems/list
"""

from typing import Any, cast, List, NotRequired, TypedDict

from backend.tasks_io.datafeeds.parsers.parser_base import ParserBase


class _PlaylistItemSnippet(TypedDict):
    """Snippet information for a playlist item."""

    title: str
    description: NotRequired[str]
    resourceId: dict  # Contains videoId, channelId, or playlistId
    playlistId: str
    position: NotRequired[int]
    publishedAt: NotRequired[str]


class _PlaylistItemId(TypedDict):
    """ID information for a playlist item."""

    kind: str  # "youtube#playlistItem"


class _PlaylistItem(TypedDict):
    """A single playlist item."""

    kind: str
    id: str
    snippet: NotRequired[_PlaylistItemSnippet]


class _PlaylistItemListResponse(TypedDict):
    """Response from playlistItems.list API call."""

    items: List[_PlaylistItem]
    nextPageToken: NotRequired[str]
    prevPageToken: NotRequired[str]
    pageInfo: NotRequired[dict]


class ParsedPlaylistItem(TypedDict):
    """Parsed playlist item - what we return to callers."""

    item_id: str
    title: str
    video_id: NotRequired[str]
    channel_id: NotRequired[str]
    playlist_id: NotRequired[str]
    position: NotRequired[int]


class YoutubePlaylistItemsParser(ParserBase[Any, List[ParsedPlaylistItem]]):
    """
    Parses YouTube playlist items from the playlistItems.list API response.

    Returns a list of parsed playlist items.
    Returns empty list if no items found.

    See: https://developers.google.com/youtube/v3/docs/playlistItems/list
    """

    def parse(self, response: Any) -> List[ParsedPlaylistItem]:
        """
        Parse playlist items from API response.

        Returns list of parsed playlist items (typically videos).
        """
        response_data = cast(_PlaylistItemListResponse, response)
        results: List[ParsedPlaylistItem] = []

        items = response_data.get("items", [])
        for item in items:
            parsed = self._parse_item(item)
            if parsed:
                results.append(parsed)

        return results

    def _parse_item(self, item: _PlaylistItem) -> "ParsedPlaylistItem | None":
        """Parse a single playlist item."""
        item_id = item.get("id", "")
        snippet = item.get("snippet")

        if not item_id or not snippet:
            return None

        title = snippet.get("title", "")
        if not title:
            return None

        result: ParsedPlaylistItem = {
            "item_id": item_id,
            "title": title,
        }

        # Extract video ID from resourceId
        resource_id = snippet.get("resourceId", {})
        if video_id := resource_id.get("videoId"):
            result["video_id"] = video_id

        if channel_id := resource_id.get("channelId"):
            result["channel_id"] = channel_id

        if playlist_id := resource_id.get("playlistId"):
            result["playlist_id"] = playlist_id

        # Add optional fields
        if position := snippet.get("position"):
            result["position"] = position

        if playlist_id := snippet.get("playlistId"):
            result["playlist_id"] = playlist_id

        return result
