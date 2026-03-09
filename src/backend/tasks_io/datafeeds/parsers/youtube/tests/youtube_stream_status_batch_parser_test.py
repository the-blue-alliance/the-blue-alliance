from backend.common.consts.webcast_status import WebcastStatus
from backend.tasks_io.datafeeds.parsers.youtube.youtube_stream_status_batch_parser import (
    YoutubeStreamStatusBatchParser,
)


def test_parser_parse_online_video() -> None:
    """Test parsing a response with an online video."""
    parser = YoutubeStreamStatusBatchParser(["video1"])

    response = {
        "items": [
            {
                "id": "video1",
                "snippet": {
                    "liveBroadcastContent": "live",
                    "title": "Live Stream Title",
                },
                "liveStreamingDetails": {
                    "concurrentViewers": 1337,
                },
            }
        ]
    }

    result = parser.parse(response)

    assert "video1" in result
    assert result["video1"]["status"] == WebcastStatus.ONLINE
    assert result["video1"]["stream_title"] == "Live Stream Title"
    assert result["video1"]["viewer_count"] == 1337


def test_parser_parse_offline_video() -> None:
    """Test parsing a response with an offline video."""
    parser = YoutubeStreamStatusBatchParser(["video1"])

    response = {
        "items": [
            {
                "id": "video1",
                "snippet": {
                    "liveBroadcastContent": "none",
                    "title": "Prerecorded Video",
                },
            }
        ]
    }

    result = parser.parse(response)

    assert "video1" in result
    assert result["video1"]["status"] == WebcastStatus.OFFLINE
    assert result["video1"]["stream_title"] == "Prerecorded Video"


def test_parser_parse_upcoming_video() -> None:
    """Test parsing a response with an upcoming video."""
    parser = YoutubeStreamStatusBatchParser(["video1"])

    response = {
        "items": [
            {
                "id": "video1",
                "snippet": {
                    "liveBroadcastContent": "upcoming",
                    "title": "Upcoming Stream",
                },
            }
        ]
    }

    result = parser.parse(response)

    assert "video1" in result
    assert result["video1"]["status"] == WebcastStatus.OFFLINE
    assert result["video1"]["stream_title"] == "Upcoming Stream"


def test_parser_parse_multiple_videos() -> None:
    """Test parsing a batch response with multiple videos."""
    parser = YoutubeStreamStatusBatchParser(["video1", "video2", "video3"])

    response = {
        "items": [
            {
                "id": "video1",
                "snippet": {
                    "liveBroadcastContent": "live",
                    "title": "Live Stream 1",
                },
                "liveStreamingDetails": {"concurrentViewers": 100},
            },
            {
                "id": "video2",
                "snippet": {
                    "liveBroadcastContent": "none",
                    "title": "Video 2",
                },
            },
            {
                "id": "video3",
                "snippet": {
                    "liveBroadcastContent": "live",
                    "title": "Live Stream 3",
                },
                "liveStreamingDetails": {"concurrentViewers": 500},
            },
        ]
    }

    result = parser.parse(response)

    assert len(result) == 3
    assert result["video1"]["status"] == WebcastStatus.ONLINE
    assert result["video1"]["viewer_count"] == 100
    assert result["video2"]["status"] == WebcastStatus.OFFLINE
    assert result["video3"]["status"] == WebcastStatus.ONLINE
    assert result["video3"]["viewer_count"] == 500


def test_parser_parse_empty_response() -> None:
    """Test parsing an empty response (no items)."""
    parser = YoutubeStreamStatusBatchParser(["video1", "video2"])

    response = {"items": []}

    result = parser.parse(response)

    # All videos should be marked as offline when not in response
    assert len(result) == 2
    assert result["video1"]["status"] == WebcastStatus.OFFLINE
    assert result["video2"]["status"] == WebcastStatus.OFFLINE


def test_parser_parse_missing_items_key() -> None:
    """Test parsing a response missing the items key."""
    parser = YoutubeStreamStatusBatchParser(["video1"])

    response = {}

    result = parser.parse(response)

    # Video should be marked as offline when not in response
    assert result["video1"]["status"] == WebcastStatus.OFFLINE


def test_parser_parse_partial_response() -> None:
    """Test parsing when only some requested videos are in the response."""
    parser = YoutubeStreamStatusBatchParser(["video1", "video2", "video3"])

    response = {
        "items": [
            {
                "id": "video1",
                "snippet": {
                    "liveBroadcastContent": "live",
                    "title": "Live 1",
                },
            },
            {
                "id": "video3",
                "snippet": {
                    "liveBroadcastContent": "none",
                    "title": "Video 3",
                },
            },
        ]
    }

    result = parser.parse(response)

    # All three should be in result
    assert len(result) == 3
    # video1 and video3 have data
    assert result["video1"]["status"] == WebcastStatus.ONLINE
    assert result["video3"]["status"] == WebcastStatus.OFFLINE
    # video2 was not in response, should be offline
    assert result["video2"]["status"] == WebcastStatus.OFFLINE


def test_parser_parse_no_viewer_count() -> None:
    """Test parsing when liveStreamingDetails doesn't have concurrentViewers."""
    parser = YoutubeStreamStatusBatchParser(["video1"])

    response = {
        "items": [
            {
                "id": "video1",
                "snippet": {
                    "liveBroadcastContent": "live",
                    "title": "Live Stream",
                },
                "liveStreamingDetails": {},
            }
        ]
    }

    result = parser.parse(response)

    assert result["video1"]["status"] == WebcastStatus.ONLINE
    assert result["video1"]["stream_title"] == "Live Stream"
    # viewer_count should not be set if not in response
    assert "viewer_count" not in result["video1"]


def test_parser_parse_live_without_details() -> None:
    """Test parsing a live video without liveStreamingDetails."""
    parser = YoutubeStreamStatusBatchParser(["video1"])

    response = {
        "items": [
            {
                "id": "video1",
                "snippet": {
                    "liveBroadcastContent": "live",
                    "title": "Live but no details",
                },
            }
        ]
    }

    result = parser.parse(response)

    assert result["video1"]["status"] == WebcastStatus.ONLINE
    assert result["video1"]["stream_title"] == "Live but no details"
    assert "viewer_count" not in result["video1"]


def test_parser_parse_missing_snippet() -> None:
    """Test parsing when snippet is missing."""
    parser = YoutubeStreamStatusBatchParser(["video1"])

    response = {
        "items": [
            {
                "id": "video1",
            }
        ]
    }

    result = parser.parse(response)

    assert result["video1"]["status"] == WebcastStatus.OFFLINE
    assert "stream_title" not in result["video1"]
