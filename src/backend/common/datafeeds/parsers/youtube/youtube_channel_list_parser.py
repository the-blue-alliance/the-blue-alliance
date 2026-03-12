"""Parser for YouTube channels.list API responses."""

from typing import Any, cast, List, NotRequired, TypedDict

from backend.common.datafeeds.parsers.parser_base import ParserBase


class _ChannelListSnippet(TypedDict):
    title: str


class _ChannelListItem(TypedDict):
    id: str
    snippet: NotRequired[_ChannelListSnippet]


class _ChannelListResponse(TypedDict):
    items: List[_ChannelListItem]


class ParsedChannelListResult(TypedDict):
    channel_id: str
    channel_name: str


class YoutubeChannelListParser(ParserBase[Any, List[ParsedChannelListResult]]):
    def parse(self, response: Any) -> List[ParsedChannelListResult]:
        response_data = cast(_ChannelListResponse, response)
        results: List[ParsedChannelListResult] = []

        for item in response_data.get("items", []):
            channel_id = item.get("id")
            snippet = item.get("snippet", {})
            channel_name = snippet.get("title")

            if not channel_id or not channel_name:
                continue

            results.append(
                ParsedChannelListResult(
                    channel_id=channel_id,
                    channel_name=channel_name,
                )
            )

        return results
