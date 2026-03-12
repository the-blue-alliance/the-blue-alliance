"""Tests for YouTube channel and search datafeeds/parsers."""

import json
from unittest import mock

import pytest

from backend.common.datafeeds.datafeed_youtube import (
    YoutubeChannelListForHandleDatafeed,
    YoutubeUpcomingStreamsDatafeed,
)
from backend.common.datafeeds.parsers.youtube.youtube_channel_list_parser import (
    YoutubeChannelListParser,
)
from backend.common.datafeeds.parsers.youtube.youtube_search_parser import (
    YoutubeSearchParser,
)
from backend.common.futures import InstantFuture
from backend.common.sitevars.google_api_secret import GoogleApiSecret
from backend.common.urlfetch import URLFetchResult


class TestYoutubeSearchParser:
    """Tests for YoutubeSearchParser."""

    def test_parse_channel_search_results(self) -> None:
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
        assert results[1]["video_id"] == "video_abc"


class TestYoutubeChannelListParser:
    def test_parse_channel_list(self) -> None:
        parser = YoutubeChannelListParser()
        response = {
            "items": [
                {
                    "id": "UCjX4WSaAFPgM2PYr-6P",
                    "snippet": {"title": "FIRST in Michigan"},
                }
            ]
        }

        results = parser.parse(response)

        assert results == [
            {
                "channel_id": "UCjX4WSaAFPgM2PYr-6P",
                "channel_name": "FIRST in Michigan",
            }
        ]

    def test_parse_channel_list_missing_fields(self) -> None:
        parser = YoutubeChannelListParser()
        response = {"items": [{"snippet": {"title": "No id"}}, {"id": "UC123"}]}

        assert parser.parse(response) == []


class TestYoutubeChannelListForHandleDatafeed:
    def test_datafeed_endpoint(self) -> None:
        with mock.patch.object(GoogleApiSecret, "secret_key", return_value="test_key"):
            datafeed = YoutubeChannelListForHandleDatafeed("@FIRSTinMichigan")
            assert datafeed.endpoint() == "channels"

    def test_datafeed_url_params(self) -> None:
        with mock.patch.object(GoogleApiSecret, "secret_key", return_value="test_key"):
            datafeed = YoutubeChannelListForHandleDatafeed("@FIRSTinMichigan")
            params = datafeed.url_params()

            assert params["part"] == "id,snippet"
            assert params["forHandle"] == "FIRSTinMichigan"

    def test_datafeed_parser(self) -> None:
        with mock.patch.object(GoogleApiSecret, "secret_key", return_value="test_key"):
            datafeed = YoutubeChannelListForHandleDatafeed("FIRSTinMichigan")
            assert isinstance(datafeed.parser(), YoutubeChannelListParser)


class TestYoutubeUpcomingStreamsDatafeed:
    def test_datafeed_endpoint(self) -> None:
        with mock.patch.object(GoogleApiSecret, "secret_key", return_value="test_key"):
            datafeed = YoutubeUpcomingStreamsDatafeed(channel_id="UC_channel_id")
            assert datafeed.endpoint() == "search"

    def test_datafeed_default_params(self) -> None:
        with mock.patch.object(GoogleApiSecret, "secret_key", return_value="test_key"):
            datafeed = YoutubeUpcomingStreamsDatafeed(channel_id="UC_channel_id")
            params = datafeed.url_params()

            assert params["part"] == "snippet"
            assert params["type"] == "video"
            assert params["channelId"] == "UC_channel_id"
            assert params["eventType"] == "upcoming"
            assert params["maxResults"] == "50"
            assert params["order"] == "date"
            assert "pageToken" not in params

    def test_datafeed_with_page_token(self) -> None:
        with mock.patch.object(GoogleApiSecret, "secret_key", return_value="test_key"):
            datafeed = YoutubeUpcomingStreamsDatafeed(
                channel_id="UC_channel_id",
                page_token="TOKEN_123",
            )
            params = datafeed.url_params()

            assert params["pageToken"] == "TOKEN_123"

    def test_datafeed_parser(self) -> None:
        with mock.patch.object(GoogleApiSecret, "secret_key", return_value="test_key"):
            datafeed = YoutubeUpcomingStreamsDatafeed(channel_id="UC_channel_id")
            assert isinstance(datafeed.parser(), YoutubeSearchParser)

    def test_fetch_all_pages_async_single_page(self, ndb_context) -> None:
        with mock.patch.object(GoogleApiSecret, "secret_key", return_value="test_key"):
            datafeed = YoutubeUpcomingStreamsDatafeed(channel_id="UC_channel_id")

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

            with mock.patch.object(
                YoutubeUpcomingStreamsDatafeed, "_fetch"
            ) as mock_fetch:
                mock_fetch.return_value = InstantFuture(mock_result)
                results = datafeed.fetch_all_pages_async().get_result()

            assert len(results) == 1
            assert results[0]["video_id"] == "video_1"
            assert results[0]["title"] == "Video 1"
            assert mock_fetch.call_count == 1

    def test_fetch_all_pages_async_pagination(self, ndb_context) -> None:
        with mock.patch.object(GoogleApiSecret, "secret_key", return_value="test_key"):
            datafeed = YoutubeUpcomingStreamsDatafeed(channel_id="UC_channel_id")

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

            with mock.patch.object(
                YoutubeUpcomingStreamsDatafeed, "_fetch"
            ) as mock_fetch:
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
            datafeed = YoutubeUpcomingStreamsDatafeed(channel_id="UC_channel_id")

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

            with mock.patch.object(
                YoutubeUpcomingStreamsDatafeed, "_fetch"
            ) as mock_fetch:
                mock_fetch.return_value = InstantFuture(mock_result)
                results = datafeed.fetch_all_pages_async().get_result()

            assert len(results) == 1
            assert results[0]["video_id"] == "video_fallback"
            assert results[0]["title"] == "Fallback Video"

    def test_fetch_all_pages_async_non_200_raises(self, ndb_context) -> None:
        with mock.patch.object(GoogleApiSecret, "secret_key", return_value="test_key"):
            datafeed = YoutubeUpcomingStreamsDatafeed(channel_id="UC_channel_id")

            mock_result = URLFetchResult.mock_for_content(
                "https://www.googleapis.com/youtube/v3/search",
                403,
                "{}",
            )

            with mock.patch.object(
                YoutubeUpcomingStreamsDatafeed, "_fetch"
            ) as mock_fetch:
                mock_fetch.return_value = InstantFuture(mock_result)
                with pytest.raises(
                    Exception,
                    match="Unable to call YouTube API for search",
                ):
                    datafeed.fetch_all_pages_async().get_result()
