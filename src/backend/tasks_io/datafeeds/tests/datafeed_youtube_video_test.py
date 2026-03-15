"""Tests for YouTube video details API datafeeds and parser."""

from unittest import mock

from backend.common.datafeeds.datafeed_youtube import YoutubeVideoDetailsDatafeed
from backend.common.datafeeds.parsers.youtube.youtube_video_details_parser import (
    YoutubeVideoDetailsParser,
)
from backend.common.sitevars.google_api_secret import GoogleApiSecret


class TestYoutubeVideoDetailsParser:
    """Tests for YoutubeVideoDetailsParser."""

    def test_parse_complete_video_details(self) -> None:
        """Test parsing a complete video details response."""
        response = {
            "items": [
                {
                    "id": "video_123",
                    "snippet": {
                        "title": "Test Video Title",
                        "description": "Test description",
                        "channelId": "channel_456",
                        "channelTitle": "Test Channel",
                    },
                    "liveStreamingDetails": {
                        "scheduledStartTime": "2024-03-08T15:30:00Z",
                        "actualStartTime": "2024-03-08T15:35:00Z",
                        "concurrentViewers": "1234",
                    },
                }
            ]
        }

        parser = YoutubeVideoDetailsParser()
        result = parser.parse(response)

        assert "video_123" in result
        details = result["video_123"]
        assert details["video_id"] == "video_123"
        assert details["title"] == "Test Video Title"
        assert details["channel_id"] == "channel_456"
        assert details["description"] == "Test description"
        assert details["scheduled_start_time"] == "2024-03-08"
        assert details["actual_start_time"] == "2024-03-08"
        assert details["concurrent_viewers"] == 1234

    def test_parse_video_without_live_details(self) -> None:
        """Test parsing a video without live streaming details."""
        response = {
            "items": [
                {
                    "id": "video_123",
                    "snippet": {
                        "title": "Regular Video",
                        "channelId": "channel_456",
                    },
                }
            ]
        }

        parser = YoutubeVideoDetailsParser()
        result = parser.parse(response)

        assert "video_123" in result
        details = result["video_123"]
        assert details["video_id"] == "video_123"
        assert details["title"] == "Regular Video"
        assert "scheduled_start_time" not in details
        assert "concurrent_viewers" not in details

    def test_parse_empty_response(self) -> None:
        """Test parsing empty response returns empty dict."""
        response = {"items": []}

        parser = YoutubeVideoDetailsParser()
        result = parser.parse(response)

        assert result == {}

    def test_parse_missing_required_fields(self) -> None:
        """Test parsing item without ID is skipped."""
        response = {
            "items": [
                {
                    "snippet": {
                        "title": "Test",
                    }
                }
            ]
        }

        parser = YoutubeVideoDetailsParser()
        result = parser.parse(response)

        assert result == {}

    def test_parse_invalid_concurrent_viewers(self) -> None:
        """Test that invalid concurrent viewers value is ignored."""
        response = {
            "items": [
                {
                    "id": "video_123",
                    "snippet": {"title": "Test"},
                    "liveStreamingDetails": {
                        "concurrentViewers": "not_a_number",
                    },
                }
            ]
        }

        parser = YoutubeVideoDetailsParser()
        result = parser.parse(response)

        assert "video_123" in result
        assert "concurrent_viewers" not in result["video_123"]

    def test_parse_multiple_videos(self) -> None:
        """Test parsing multiple video items returns all of them."""
        response = {
            "items": [
                {
                    "id": "video_1",
                    "snippet": {"title": "Video 1"},
                    "liveStreamingDetails": {
                        "scheduledStartTime": "2024-03-08T15:00:00Z",
                    },
                },
                {
                    "id": "video_2",
                    "snippet": {"title": "Video 2"},
                },
            ]
        }

        parser = YoutubeVideoDetailsParser()
        result = parser.parse(response)

        assert "video_1" in result
        assert "video_2" in result
        assert result["video_1"]["scheduled_start_time"] == "2024-03-08"
        assert "scheduled_start_time" not in result["video_2"]

    def test_parse_absent_video_not_in_result(self) -> None:
        """Test that a video ID not in the response is absent from the result dict."""
        response = {
            "items": [
                {
                    "id": "video_1",
                    "snippet": {"title": "Video 1"},
                },
            ]
        }

        parser = YoutubeVideoDetailsParser()
        result = parser.parse(response)

        assert "video_1" in result
        assert "video_2" not in result


class TestYoutubeVideoDetailsDatafeed:
    """Tests for YoutubeVideoDetailsDatafeed."""

    def test_datafeed_initialization(self) -> None:
        """Test datafeed initializes with video IDs."""
        with mock.patch.object(GoogleApiSecret, "secret_key", return_value="test_key"):
            datafeed = YoutubeVideoDetailsDatafeed(["video_123"])
            assert datafeed.video_ids == ["video_123"]

    def test_datafeed_endpoint(self) -> None:
        """Test datafeed returns correct endpoint."""
        with mock.patch.object(GoogleApiSecret, "secret_key", return_value="test_key"):
            datafeed = YoutubeVideoDetailsDatafeed(["video_123"])
            assert datafeed.endpoint() == "videos"

    def test_datafeed_url_params(self) -> None:
        """Test datafeed constructs correct URL parameters."""
        with mock.patch.object(GoogleApiSecret, "secret_key", return_value="test_key"):
            datafeed = YoutubeVideoDetailsDatafeed(["video_456"])
            params = datafeed.url_params()

            assert params["part"] == "snippet,liveStreamingDetails"
            assert params["id"] == "video_456"

    def test_datafeed_url_params_multiple(self) -> None:
        """Test datafeed constructs correct URL parameters for multiple IDs."""
        with mock.patch.object(GoogleApiSecret, "secret_key", return_value="test_key"):
            datafeed = YoutubeVideoDetailsDatafeed(["video_1", "video_2"])
            params = datafeed.url_params()

            assert params["part"] == "snippet,liveStreamingDetails"
            assert params["id"] == "video_1,video_2"

    def test_datafeed_url_construction(self) -> None:
        """Test complete URL construction."""
        with mock.patch.object(GoogleApiSecret, "secret_key", return_value="test_key"):
            datafeed = YoutubeVideoDetailsDatafeed(["video_789"])
            url = datafeed.url()

            assert "videos" in url
            assert "video_789" in url
            assert "snippet,liveStreamingDetails" in url

    def test_datafeed_parser(self) -> None:
        """Test datafeed returns correct parser instance."""
        with mock.patch.object(GoogleApiSecret, "secret_key", return_value="test_key"):
            datafeed = YoutubeVideoDetailsDatafeed(["video_123"])
            parser = datafeed.parser()

            assert isinstance(parser, YoutubeVideoDetailsParser)
