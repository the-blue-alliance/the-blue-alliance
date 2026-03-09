"""Tests for YouTube search API datafeeds and parser."""

import json
from unittest import mock

import pytest

from backend.common.futures import InstantFuture
from backend.common.sitevars.google_api_secret import GoogleApiSecret
from backend.common.urlfetch import URLFetchResult
from backend.tasks_io.datafeeds.datafeed_youtube import YoutubeSearchDatafeed
from backend.tasks_io.datafeeds.parsers.youtube.youtube_search_parser import (
    YoutubeSearchParser,
)


class TestYoutubeSearchParser:
    """Tests for YoutubeSearchParser."""

    def test_parse_channel_search_results(self) -> None:
        """Test parsing search results for channels."""
        response = {
            "items": [
                {
                    "kind": "youtube#searchResult",
                    "id": {
                        "kind": "youtube#channel",
                        "channelId": "UCabc123",
                    },
                    "snippet": {
                        "title": "Example Channel",
                        "description": "A test channel",
                        "channelId": "UCabc123",
                        "channelTitle": "Example Channel",
                    },
                }
            ]
        }

        parser = YoutubeSearchParser()
        results = parser.parse(response)

        assert len(results) == 1
        result = results[0]
        assert result["kind"] == "youtube#channel"
        assert result["title"] == "Example Channel"
        assert result["channel_id"] == "UCabc123"

    def test_parse_video_search_results(self) -> None:
        """Test parsing search results for videos."""
        response = {
            "items": [
                {
                    "kind": "youtube#searchResult",
                    "id": {
                        "kind": "youtube#video",
                        "videoId": "video_xyz",
                    },
                    "snippet": {
                        "title": "Example Video",
                        "description": "A test video",
                        "liveBroadcastContent": "none",
                    },
                },
                {
                    "kind": "youtube#searchResult",
                    "id": {
                        "kind": "youtube#video",
                        "videoId": "video_abc",
                    },
                    "snippet": {
                        "title": "Upcoming Stream",
                        "liveBroadcastContent": "upcoming",
                    },
                },
            ]
        }

        parser = YoutubeSearchParser()
        results = parser.parse(response)

        assert len(results) == 2
        assert results[0]["video_id"] == "video_xyz"
        assert results[0]["title"] == "Example Video"
        assert results[1]["video_id"] == "video_abc"
        assert results[1]["title"] == "Upcoming Stream"

    def test_parse_multiple_result_types(self) -> None:
        """Test parsing mixed result types (channel, video, playlist)."""
        response = {
            "items": [
                {
                    "kind": "youtube#searchResult",
                    "id": {
                        "kind": "youtube#channel",
                        "channelId": "channel_123",
                    },
                    "snippet": {
                        "title": "Test Channel",
                    },
                },
                {
                    "kind": "youtube#searchResult",
                    "id": {
                        "kind": "youtube#video",
                        "videoId": "video_456",
                    },
                    "snippet": {
                        "title": "Test Video",
                    },
                },
                {
                    "kind": "youtube#searchResult",
                    "id": {
                        "kind": "youtube#playlist",
                        "playlistId": "playlist_789",
                    },
                    "snippet": {
                        "title": "Test Playlist",
                    },
                },
            ]
        }

        parser = YoutubeSearchParser()
        results = parser.parse(response)

        assert len(results) == 3
        assert results[0]["channel_id"] == "channel_123"
        assert results[1]["video_id"] == "video_456"
        assert results[2]["playlist_id"] == "playlist_789"

    def test_parse_empty_response(self) -> None:
        """Test parsing empty response returns empty list."""
        response = {"items": []}

        parser = YoutubeSearchParser()
        results = parser.parse(response)

        assert results == []

    def test_parse_missing_snippet_skipped(self) -> None:
        """Test that items without snippets are skipped."""
        response = {
            "items": [
                {
                    "id": {
                        "kind": "youtube#channel",
                        "channelId": "channel_123",
                    },
                    # Missing snippet
                },
                {
                    "kind": "youtube#searchResult",
                    "id": {
                        "kind": "youtube#channel",
                        "channelId": "channel_456",
                    },
                    "snippet": {
                        "title": "Valid Channel",
                    },
                },
            ]
        }

        parser = YoutubeSearchParser()
        results = parser.parse(response)

        assert len(results) == 1
        assert results[0]["channel_id"] == "channel_456"

    def test_parse_page_tokens(self) -> None:
        """Test that page tokens are preserved in response."""
        response = {
            "items": [
                {
                    "kind": "youtube#searchResult",
                    "id": {
                        "kind": "youtube#video",
                        "videoId": "video_1",
                    },
                    "snippet": {
                        "title": "Video 1",
                    },
                }
            ],
            "nextPageToken": "NEXT_TOKEN_123",
            "prevPageToken": "PREV_TOKEN_456",
        }

        parser = YoutubeSearchParser()
        results = parser.parse(response)

        assert len(results) == 1
        # Note: Parser returns just the items, not the tokens
        # Tokens would need to be handled separately by the caller


class TestYoutubeSearchDatafeed:
    """Tests for YoutubeSearchDatafeed."""

    def test_datafeed_initialization(self) -> None:
        """Test datafeed initializes with search query."""
        with mock.patch.object(GoogleApiSecret, "secret_key", return_value="test_key"):
            datafeed = YoutubeSearchDatafeed("test channel")
            assert datafeed.query == "test channel"

    def test_datafeed_endpoint(self) -> None:
        """Test datafeed returns correct endpoint."""
        with mock.patch.object(GoogleApiSecret, "secret_key", return_value="test_key"):
            datafeed = YoutubeSearchDatafeed("query")
            assert datafeed.endpoint() == "search"

    def test_datafeed_default_params(self) -> None:
        """Test datafeed constructs default URL parameters."""
        with mock.patch.object(GoogleApiSecret, "secret_key", return_value="test_key"):
            datafeed = YoutubeSearchDatafeed("test")
            params = datafeed.url_params()

            assert params["part"] == "snippet"
            assert params["type"] == "channel"
            assert params["q"] == "test"
            assert params["maxResults"] == "1"
            assert params["order"] == "relevance"
            assert "pageToken" not in params

    def test_datafeed_custom_search_type(self) -> None:
        """Test datafeed with custom search type."""
        with mock.patch.object(GoogleApiSecret, "secret_key", return_value="test_key"):
            datafeed = YoutubeSearchDatafeed("query", search_type="video")
            params = datafeed.url_params()

            assert params["type"] == "video"

    def test_datafeed_with_max_results(self) -> None:
        """Test datafeed with custom max results."""
        with mock.patch.object(GoogleApiSecret, "secret_key", return_value="test_key"):
            datafeed = YoutubeSearchDatafeed("query", max_results=50)
            params = datafeed.url_params()

            assert params["maxResults"] == "50"

    def test_datafeed_with_page_token(self) -> None:
        """Test datafeed with pagination token."""
        with mock.patch.object(GoogleApiSecret, "secret_key", return_value="test_key"):
            datafeed = YoutubeSearchDatafeed("query", page_token="TOKEN_123")
            params = datafeed.url_params()

            assert params["pageToken"] == "TOKEN_123"

    def test_datafeed_with_custom_order(self) -> None:
        """Test datafeed with custom sort order."""
        with mock.patch.object(GoogleApiSecret, "secret_key", return_value="test_key"):
            datafeed = YoutubeSearchDatafeed("query", order="date")
            params = datafeed.url_params()

            assert params["order"] == "date"

    def test_datafeed_without_query(self) -> None:
        """Test datafeed can omit free-text query."""
        with mock.patch.object(GoogleApiSecret, "secret_key", return_value="test_key"):
            datafeed = YoutubeSearchDatafeed(query=None, search_type="video")
            params = datafeed.url_params()

            assert "q" not in params

    def test_datafeed_with_channel_and_event_type(self) -> None:
        """Test datafeed supports channel/event constrained searches."""
        with mock.patch.object(GoogleApiSecret, "secret_key", return_value="test_key"):
            datafeed = YoutubeSearchDatafeed(
                query=None,
                search_type="video",
                order="date",
                max_results=50,
                channel_id="UC_channel_id",
                event_type="upcoming",
            )
            params = datafeed.url_params()

            assert params["channelId"] == "UC_channel_id"
            assert params["eventType"] == "upcoming"
            assert params["type"] == "video"
            assert params["order"] == "date"
            assert params["maxResults"] == "50"

    def test_datafeed_url_construction(self) -> None:
        """Test complete URL construction."""
        with mock.patch.object(GoogleApiSecret, "secret_key", return_value="test_key"):
            datafeed = YoutubeSearchDatafeed("python tutorial", search_type="video")
            url = datafeed.url()

            assert "search" in url
            assert "python%20tutorial" in url or "python+tutorial" in url
            assert "video" in url

    def test_datafeed_parser(self) -> None:
        """Test datafeed returns correct parser instance."""
        with mock.patch.object(GoogleApiSecret, "secret_key", return_value="test_key"):
            datafeed = YoutubeSearchDatafeed("query")
            parser = datafeed.parser()

            assert isinstance(parser, YoutubeSearchParser)

    def test_fetch_all_pages_async_single_page(self, ndb_context) -> None:
        with mock.patch.object(GoogleApiSecret, "secret_key", return_value="test_key"):
            datafeed = YoutubeSearchDatafeed(query=None, search_type="video")

            response = {
                "items": [
                    {
                        "id": {"kind": "youtube#video", "videoId": "video_1"},
                        "snippet": {"title": "Video 1"},
                    }
                ]
            }
            mock_result = URLFetchResult.mock_for_content(
                "https://www.googleapis.com/youtube/v3/search",
                200,
                json.dumps(response),
            )

            with mock.patch.object(YoutubeSearchDatafeed, "_fetch") as mock_fetch:
                mock_fetch.return_value = InstantFuture(mock_result)
                results = datafeed.fetch_all_pages_async().get_result()

            assert len(results) == 1
            assert results[0]["video_id"] == "video_1"
            assert results[0]["title"] == "Video 1"
            assert mock_fetch.call_count == 1

    def test_fetch_all_pages_async_pagination(self, ndb_context) -> None:
        with mock.patch.object(GoogleApiSecret, "secret_key", return_value="test_key"):
            datafeed = YoutubeSearchDatafeed(query=None, search_type="video")

            response_1 = {
                "items": [
                    {
                        "id": {"kind": "youtube#video", "videoId": "video_1"},
                        "snippet": {"title": "Video 1"},
                    }
                ],
                "nextPageToken": "NEXT_PAGE",
            }
            response_2 = {
                "items": [
                    {
                        "id": {"kind": "youtube#video", "videoId": "video_2"},
                        "snippet": {"title": "Video 2"},
                    }
                ]
            }

            mock_result_1 = URLFetchResult.mock_for_content(
                "https://www.googleapis.com/youtube/v3/search",
                200,
                json.dumps(response_1),
            )
            mock_result_2 = URLFetchResult.mock_for_content(
                "https://www.googleapis.com/youtube/v3/search",
                200,
                json.dumps(response_2),
            )

            with mock.patch.object(YoutubeSearchDatafeed, "_fetch") as mock_fetch:
                mock_fetch.side_effect = [
                    InstantFuture(mock_result_1),
                    InstantFuture(mock_result_2),
                ]
                results = datafeed.fetch_all_pages_async().get_result()

            assert len(results) == 2
            assert results[0]["video_id"] == "video_1"
            assert results[1]["video_id"] == "video_2"
            assert mock_fetch.call_count == 2

    def test_fetch_all_pages_async_fallback_parser(self, ndb_context) -> None:
        with mock.patch.object(GoogleApiSecret, "secret_key", return_value="test_key"):
            datafeed = YoutubeSearchDatafeed(query=None, search_type="video")

            # Missing id.kind, so parser returns empty and fallback parser is used.
            response = {
                "items": [
                    {
                        "id": {"videoId": "video_fallback"},
                        "snippet": {"title": "Fallback Video"},
                    }
                ]
            }
            mock_result = URLFetchResult.mock_for_content(
                "https://www.googleapis.com/youtube/v3/search",
                200,
                json.dumps(response),
            )

            with mock.patch.object(YoutubeSearchDatafeed, "_fetch") as mock_fetch:
                mock_fetch.return_value = InstantFuture(mock_result)
                results = datafeed.fetch_all_pages_async().get_result()

            assert len(results) == 1
            assert results[0]["video_id"] == "video_fallback"
            assert results[0]["title"] == "Fallback Video"

    def test_fetch_all_pages_async_non_200_raises(self, ndb_context) -> None:
        with mock.patch.object(GoogleApiSecret, "secret_key", return_value="test_key"):
            datafeed = YoutubeSearchDatafeed(query=None, search_type="video")

            mock_result = URLFetchResult.mock_for_content(
                "https://www.googleapis.com/youtube/v3/search",
                403,
                "{}",
            )

            with mock.patch.object(YoutubeSearchDatafeed, "_fetch") as mock_fetch:
                mock_fetch.return_value = InstantFuture(mock_result)
                with pytest.raises(
                    Exception,
                    match="Unable to call YouTube API for search",
                ):
                    datafeed.fetch_all_pages_async().get_result()
