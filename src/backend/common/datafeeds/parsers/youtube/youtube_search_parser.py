"""Parser for YouTube search API response.

Follows YouTube Data API v3 schema:
https://developers.google.com/youtube/v3/docs/search/list
"""

from typing import Any, cast, List, NotRequired, TypedDict

from backend.common.datafeeds.parsers.parser_base import ParserBase


class _SearchResultId(TypedDict):
    """ID information for a search result."""

    kind: str  # "youtube#video", "youtube#channel", "youtube#playlist"
    videoId: NotRequired[str]
    channelId: NotRequired[str]
    playlistId: NotRequired[str]


class _SearchResultSnippet(TypedDict):
    """Snippet information in a search result."""

    title: str
    description: NotRequired[str]
    channelId: NotRequired[str]
    channelTitle: NotRequired[str]
    liveBroadcastContent: NotRequired[str]  # "none", "upcoming", "live"
    publishedAt: NotRequired[str]


class _SearchResult(TypedDict):
    """A single search result item."""

    kind: str
    id: _SearchResultId
    snippet: NotRequired[_SearchResultSnippet]


class _SearchListResponse(TypedDict):
    """Response from search.list API call."""

    items: List[_SearchResult]
    nextPageToken: NotRequired[str]
    prevPageToken: NotRequired[str]
    pageInfo: NotRequired[dict]


class ParsedSearchResult(TypedDict):
    """Parsed search result - what we return to callers."""

    kind: str  # "youtube#video", "youtube#channel", "youtube#playlist"
    title: str
    channel_id: NotRequired[str]
    video_id: NotRequired[str]
    playlist_id: NotRequired[str]
    description: NotRequired[str]


class YoutubeSearchParser(ParserBase[Any, List[ParsedSearchResult]]):
    """
    Parses YouTube search results from the search.list API response.

    Returns a list of parsed search results.
    Returns empty list if no items found.

    See: https://developers.google.com/youtube/v3/docs/search/list
    """

    def parse(self, response: Any) -> List[ParsedSearchResult]:
        """
        Parse search results from API response.

        Returns list of parsed search results.
        """
        response_data = cast(_SearchListResponse, response)
        results: List[ParsedSearchResult] = []

        items = response_data.get("items", [])
        for item in items:
            parsed = self._parse_item(item)
            if parsed:
                results.append(parsed)

        return results

    def _parse_item(self, item: _SearchResult) -> "ParsedSearchResult | None":
        """Parse a single search result item."""
        item_id = item.get("id")
        snippet = item.get("snippet")

        if not item_id or not snippet:
            return None

        kind = item_id.get("kind", "")
        title = snippet.get("title", "")

        if not kind or not title:
            return None

        result: ParsedSearchResult = {
            "kind": kind,
            "title": title,
        }

        if video_id := item_id.get("videoId"):
            result["video_id"] = video_id

        if channel_id := item_id.get("channelId"):
            result["channel_id"] = channel_id

        if "channel_id" not in result:
            if snippet_channel_id := snippet.get("channelId"):
                result["channel_id"] = snippet_channel_id

        if playlist_id := item_id.get("playlistId"):
            result["playlist_id"] = playlist_id

        if description := snippet.get("description"):
            result["description"] = description

        return result
