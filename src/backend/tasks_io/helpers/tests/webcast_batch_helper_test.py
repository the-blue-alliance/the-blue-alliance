from unittest.mock import Mock, patch

import pytest
from freezegun import freeze_time

from backend.common.consts.webcast_status import WebcastStatus
from backend.common.consts.webcast_type import WebcastType
from backend.common.datafeeds.datafeed_youtube import YoutubeWebcastStatusBatch
from backend.common.datafeeds.parsers.youtube.youtube_stream_status_batch_parser import (
    _BroadcastType,
    _StreamStatusResponseBatch,
    YoutubeStreamStatusBatchParser,
)
from backend.common.models.webcast import Webcast, WebcastOnlineStatus


@pytest.fixture(autouse=True)
def auto_add_ndb_stub(ndb_stub) -> None:
    pass


class TestYoutubeStreamStatusBatchParser:
    def test_parse_multiple_livestreams(self) -> None:
        """Test parsing multiple YouTube livestreams returns status data only."""
        video_ids = ["video1", "video2", "video3"]
        parser = YoutubeStreamStatusBatchParser(video_ids)
        response: _StreamStatusResponseBatch = {
            "items": [
                {
                    "id": "video1",
                    "snippet": {
                        "liveBroadcastContent": _BroadcastType.LIVE,
                        "title": "Stream 1",
                    },
                    "liveStreamingDetails": {"concurrentViewers": 1000},
                },
                {
                    "id": "video2",
                    "snippet": {
                        "liveBroadcastContent": _BroadcastType.NONE,
                        "title": "Stream 2",
                    },
                },
                {
                    "id": "video3",
                    "snippet": {
                        "liveBroadcastContent": _BroadcastType.UPCOMING,
                        "title": "Stream 3",
                    },
                },
            ]
        }

        result = parser.parse(response)

        assert len(result) == 3
        # Verify results are just status data, not full webcasts
        assert result["video1"]["status"] == WebcastStatus.ONLINE
        assert result["video1"]["stream_title"] == "Stream 1"
        assert result["video1"]["viewer_count"] == 1000
        assert "type" not in result["video1"]  # No webcast type
        assert "channel" not in result["video1"]  # No channel

        assert result["video2"]["status"] == WebcastStatus.OFFLINE
        assert result["video2"]["stream_title"] == "Stream 2"
        assert result["video3"]["status"] == WebcastStatus.OFFLINE

    def test_parse_partial_response(self) -> None:
        """Test parsing when some IDs are missing from response."""
        video_ids = ["video1", "video2", "video3"]
        parser = YoutubeStreamStatusBatchParser(video_ids)
        response: _StreamStatusResponseBatch = {
            "items": [
                {
                    "id": "video1",
                    "snippet": {
                        "liveBroadcastContent": _BroadcastType.LIVE,
                        "title": "Stream 1",
                    },
                }
            ]
        }

        result = parser.parse(response)

        assert len(result) == 3
        assert result["video1"]["status"] == WebcastStatus.ONLINE
        # Missing videos should be marked offline
        assert result["video2"]["status"] == WebcastStatus.OFFLINE
        assert result["video3"]["status"] == WebcastStatus.OFFLINE

    def test_parse_empty_response(self) -> None:
        """Test parsing empty response."""
        video_ids = ["video1", "video2"]
        parser = YoutubeStreamStatusBatchParser(video_ids)
        response: _StreamStatusResponseBatch = {"items": []}

        result = parser.parse(response)

        assert len(result) == 2
        assert result["video1"]["status"] == WebcastStatus.OFFLINE
        assert result["video2"]["status"] == WebcastStatus.OFFLINE


@freeze_time("2025-04-01")
@patch("backend.common.datafeeds.datafeed_youtube.GoogleApiSecret.secret_key")
def test_youtube_webcast_status_batch_url(api_key_mock: Mock) -> None:
    """Test that YoutubeWebcastStatusBatch constructs URL and headers correctly."""
    api_key_mock.return_value = "test_api_key"

    webcasts = [
        Webcast(type=WebcastType.YOUTUBE, channel="video1"),
        Webcast(type=WebcastType.YOUTUBE, channel="video2"),
        Webcast(type=WebcastType.YOUTUBE, channel="video3"),
    ]
    batch = YoutubeWebcastStatusBatch(webcasts)
    url = batch.url()
    headers = batch.headers()

    assert "video1,video2,video3" in url
    assert "part=snippet,liveStreamingDetails" in url
    assert "key=" not in url
    assert headers == {"X-goog-api-key": "test_api_key"}


class TestYoutubeWebcastBatchMerge:
    def test_webcast_update_with_status_data(self) -> None:
        """Test that webcast.update() properly merges WebcastOnlineStatus data."""
        webcast = Webcast(type=WebcastType.YOUTUBE, channel="video1")
        status_data = WebcastOnlineStatus(
            status=WebcastStatus.ONLINE,
            stream_title="Live Stream",
            viewer_count=500,
        )

        # Merge status data into webcast
        webcast.update(status_data)

        # Verify fields were set correctly
        assert webcast["status"] == WebcastStatus.ONLINE
        assert webcast["stream_title"] == "Live Stream"
        assert webcast["viewer_count"] == 500
        assert webcast["channel"] == "video1"  # Original data preserved
        assert webcast["type"] == WebcastType.YOUTUBE  # Original data preserved
