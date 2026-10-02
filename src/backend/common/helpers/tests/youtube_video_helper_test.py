import json
import os
from unittest.mock import patch

import pytest
from _pytest.monkeypatch import MonkeyPatch

from backend.common.datafeeds.datafeed_youtube import (
    YoutubeUpcomingStreamsDatafeed,
    YoutubeVideoDetailsDatafeed,
)
from backend.common.futures import InstantFuture
from backend.common.helpers.youtube_video_helper import (
    YouTubeChannel,
    YouTubePlaylistItem,
    YouTubeUpcomingStream,
    YouTubeVideoHelper,
)
from backend.common.sitevars.google_api_secret import GoogleApiSecret
from backend.common.urlfetch import URLFetchResult


def test_parse_id_from_url() -> None:
    # Standard HTTP
    assert (
        YouTubeVideoHelper.parse_id_from_url(
            "http://www.youtube.com/watch?v=1v8_2dW7Kik"
        )
        == "1v8_2dW7Kik"
    )
    # Standard HTTPS
    assert (
        YouTubeVideoHelper.parse_id_from_url(
            "https://www.youtube.com/watch?v=1v8_2dW7Kik"
        )
        == "1v8_2dW7Kik"
    )

    # Short link HTTP
    assert (
        YouTubeVideoHelper.parse_id_from_url("http://youtu.be/1v8_2dW7Kik")
        == "1v8_2dW7Kik"
    )
    # Short link HTTPS
    assert (
        YouTubeVideoHelper.parse_id_from_url("https://youtu.be/1v8_2dW7Kik")
        == "1v8_2dW7Kik"
    )

    # YouTube Shorts
    assert (
        YouTubeVideoHelper.parse_id_from_url(
            "https://www.youtube.com/shorts/S8m53ArvTRc"
        )
        == "S8m53ArvTRc"
    )
    # YouTube Shorts without www
    assert (
        YouTubeVideoHelper.parse_id_from_url("https://youtube.com/shorts/S8m53ArvTRc")
        == "S8m53ArvTRc"
    )

    # Standard with start time
    assert (
        YouTubeVideoHelper.parse_id_from_url(
            "https://www.youtube.com/watch?v=1v8_2dW7Kik&t=21"
        )
        == "1v8_2dW7Kik?t=21"
    )
    # Short link with start time
    assert (
        YouTubeVideoHelper.parse_id_from_url("https://youtu.be/1v8_2dW7Kik?t=21")
        == "1v8_2dW7Kik?t=21"
    )

    # Many URL params
    assert (
        YouTubeVideoHelper.parse_id_from_url(
            "https://www.youtube.com/watch?v=1v8_2dW7Kik&feature=youtu.be"
        )
        == "1v8_2dW7Kik"
    )
    # Short link many URL params
    assert (
        YouTubeVideoHelper.parse_id_from_url(
            "https://youtu.be/1v8_2dW7Kik?feature=youtu.be"
        )
        == "1v8_2dW7Kik"
    )

    # Many URL params with start time
    assert (
        YouTubeVideoHelper.parse_id_from_url(
            "https://www.youtube.com/watch?v=1v8_2dW7Kik&feature=youtu.be&t=11850"
        )
        == "1v8_2dW7Kik?t=11850"
    )
    # Short link many URL params with start time
    assert (
        YouTubeVideoHelper.parse_id_from_url(
            "https://youtu.be/1v8_2dW7Kik?feature=youtu.be&t=11850"
        )
        == "1v8_2dW7Kik?t=11850"
    )

    # Bunch of inconsistent (partially outdated) formats
    assert (
        YouTubeVideoHelper.parse_id_from_url(
            "https://www.youtube.com/watch?v=1v8_2dW7Kik#t=11850"
        )
        == "1v8_2dW7Kik?t=11850"
    )
    assert (
        YouTubeVideoHelper.parse_id_from_url(
            "https://www.youtube.com/watch?v=1v8_2dW7Kik#t=1h"
        )
        == "1v8_2dW7Kik?t=3600"
    )
    assert (
        YouTubeVideoHelper.parse_id_from_url(
            "https://www.youtube.com/watch?v=1v8_2dW7Kik#t=1h1m"
        )
        == "1v8_2dW7Kik?t=3660"
    )
    assert (
        YouTubeVideoHelper.parse_id_from_url(
            "https://www.youtube.com/watch?v=1v8_2dW7Kik#t=3h17m30s"
        )
        == "1v8_2dW7Kik?t=11850"
    )
    assert (
        YouTubeVideoHelper.parse_id_from_url(
            "https://www.youtube.com/watch?v=1v8_2dW7Kik#t=1m"
        )
        == "1v8_2dW7Kik?t=60"
    )
    assert (
        YouTubeVideoHelper.parse_id_from_url(
            "https://www.youtube.com/watch?v=1v8_2dW7Kik#t=1m1s"
        )
        == "1v8_2dW7Kik?t=61"
    )
    assert (
        YouTubeVideoHelper.parse_id_from_url(
            "https://www.youtube.com/watch?v=1v8_2dW7Kik#t=1s"
        )
        == "1v8_2dW7Kik?t=1"
    )

    # Bunch of inconsistent (partially outdated) formats with short links
    assert (
        YouTubeVideoHelper.parse_id_from_url("https://youtu.be/1v8_2dW7Kik#t=11850")
        == "1v8_2dW7Kik?t=11850"
    )
    assert (
        YouTubeVideoHelper.parse_id_from_url("https://youtu.be/1v8_2dW7Kik#t=1h")
        == "1v8_2dW7Kik?t=3600"
    )
    assert (
        YouTubeVideoHelper.parse_id_from_url("https://youtu.be/1v8_2dW7Kik#t=1h1m")
        == "1v8_2dW7Kik?t=3660"
    )
    assert (
        YouTubeVideoHelper.parse_id_from_url("https://youtu.be/1v8_2dW7Kik#t=3h17m30s")
        == "1v8_2dW7Kik?t=11850"
    )
    assert (
        YouTubeVideoHelper.parse_id_from_url("https://youtu.be/1v8_2dW7Kik#t=1m")
        == "1v8_2dW7Kik?t=60"
    )
    assert (
        YouTubeVideoHelper.parse_id_from_url("https://youtu.be/1v8_2dW7Kik#t=1m1s")
        == "1v8_2dW7Kik?t=61"
    )
    assert (
        YouTubeVideoHelper.parse_id_from_url("https://youtu.be/1v8_2dW7Kik#t=1s")
        == "1v8_2dW7Kik?t=1"
    )

    # Not sure where this comes from, but it can happen
    assert (
        YouTubeVideoHelper.parse_id_from_url("https://youtu.be/1v8_2dW7Kik?t=3h17m30s")
        == "1v8_2dW7Kik?t=11850"
    )
    assert (
        YouTubeVideoHelper.parse_id_from_url(
            "https://www.youtube.com/watch?v=1v8_2dW7Kik&t=3h17m30s"
        )
        == "1v8_2dW7Kik?t=11850"
    )


@pytest.mark.parametrize(
    "title,expected_partial",
    [
        ("2020ctwat qm4", "qm4"),
        ("2020ctwat_qm4", "qm4"),
        ("2020ctwat Q4", "qm4"),
        ("CTWAT QM4", "qm4"),
        ("2020ctwat sf1m2", "sf1m2"),
        ("2020ctwat sf10m1", "sf10m1"),
        ("2020ctwat QF2M3", "qf2m3"),
        ("CTWAT F1M3", "f1m3"),
        ("asdf", ""),
    ],
)
def test_guess_match_partial_from_title(title: str, expected_partial: str) -> None:
    partial = YouTubeVideoHelper.guessMatchPartial(title)
    assert partial == expected_partial


@pytest.mark.parametrize(
    "time,expected_seconds",
    [
        ("3h17m30s", 11850),
        ("3h", 10800),
        ("10m", 600),
        ("30s", 30),
        ("asdf", 0),
    ],
)
def test_time_to_seconds(time: str, expected_seconds: int) -> None:
    seconds = YouTubeVideoHelper.time_to_seconds(time)
    assert seconds == expected_seconds


@pytest.fixture
def mock_google_api_secret(monkeypatch: MonkeyPatch) -> None:
    def mock_secret():
        return "google_api_secret"

    monkeypatch.setattr(GoogleApiSecret, "secret_key", mock_secret)


def test_get_scheduled_start_times_no_secret(ndb_context) -> None:
    result = YouTubeVideoHelper.get_scheduled_start_times(["abc123"]).get_result()
    assert result == {}


def test_get_scheduled_start_times_api_error(
    ndb_context, mock_google_api_secret
) -> None:
    mock_urlfetch_result = URLFetchResult.mock_for_content(
        "https://www.googleapis.com/youtube/v3/videos",
        403,
        "{}",
    )
    mock_future = InstantFuture(mock_urlfetch_result)

    with patch("google.appengine.ext.ndb.Context.urlfetch", return_value=mock_future):
        result = YouTubeVideoHelper.get_scheduled_start_times(["abc123"]).get_result()
    assert result == {}


def test_get_scheduled_start_times_no_items(
    ndb_context, mock_google_api_secret
) -> None:
    mock_urlfetch_result = URLFetchResult.mock_for_content(
        "https://www.googleapis.com/youtube/v3/videos",
        200,
        '{"items": []}',
    )
    mock_future = InstantFuture(mock_urlfetch_result)

    with patch("google.appengine.ext.ndb.Context.urlfetch", return_value=mock_future):
        result = YouTubeVideoHelper.get_scheduled_start_times(["abc123"]).get_result()
    assert result == {}


def test_get_scheduled_start_times_no_live_details(
    ndb_context, mock_google_api_secret
) -> None:
    mock_urlfetch_result = URLFetchResult.mock_for_content(
        "https://www.googleapis.com/youtube/v3/videos",
        200,
        '{"items": [{}]}',
    )
    mock_future = InstantFuture(mock_urlfetch_result)

    with patch("google.appengine.ext.ndb.Context.urlfetch", return_value=mock_future):
        result = YouTubeVideoHelper.get_scheduled_start_times(["abc123"]).get_result()
    assert result == {}


def test_get_scheduled_start_times_no_scheduled_time(
    ndb_context, mock_google_api_secret
) -> None:
    mock_urlfetch_result = URLFetchResult.mock_for_content(
        "https://www.googleapis.com/youtube/v3/videos",
        200,
        '{"items": [{"liveStreamingDetails": {}}]}',
    )
    mock_future = InstantFuture(mock_urlfetch_result)

    with patch("google.appengine.ext.ndb.Context.urlfetch", return_value=mock_future):
        result = YouTubeVideoHelper.get_scheduled_start_times(["abc123"]).get_result()
    assert result == {}


def test_get_scheduled_start_times_single_success(
    ndb_context, mock_google_api_secret
) -> None:
    api_resp = {
        "items": [
            {
                "id": "abc123",
                "liveStreamingDetails": {
                    "scheduledStartTime": "2023-03-15T18:00:00Z",
                },
            }
        ]
    }
    mock_urlfetch_result = URLFetchResult.mock_for_content(
        "https://www.googleapis.com/youtube/v3/videos",
        200,
        json.dumps(api_resp),
    )
    mock_future = InstantFuture(mock_urlfetch_result)

    with patch("google.appengine.ext.ndb.Context.urlfetch", return_value=mock_future):
        result = YouTubeVideoHelper.get_scheduled_start_times(["abc123"]).get_result()
    assert result == {"abc123": "2023-03-15"}


def test_get_scheduled_start_times_prefers_later_actual_date(
    ndb_context, mock_google_api_secret
) -> None:
    api_resp = {
        "items": [
            {
                "id": "abc123",
                "liveStreamingDetails": {
                    "scheduledStartTime": "2023-03-15T23:00:00Z",
                    "actualStartTime": "2023-03-16T00:05:00Z",
                },
            }
        ]
    }
    mock_urlfetch_result = URLFetchResult.mock_for_content(
        "https://www.googleapis.com/youtube/v3/videos",
        200,
        json.dumps(api_resp),
    )
    mock_future = InstantFuture(mock_urlfetch_result)

    with patch("google.appengine.ext.ndb.Context.urlfetch", return_value=mock_future):
        result = YouTubeVideoHelper.get_scheduled_start_times(["abc123"]).get_result()
    assert result == {"abc123": "2023-03-16"}


def test_get_scheduled_start_times_keep_scheduled_for_earlier_actual_date(
    ndb_context, mock_google_api_secret
) -> None:
    api_resp = {
        "items": [
            {
                "id": "abc123",
                "liveStreamingDetails": {
                    "scheduledStartTime": "2023-03-16T00:05:00Z",
                    "actualStartTime": "2023-03-15T23:00:00Z",
                },
            }
        ]
    }
    mock_urlfetch_result = URLFetchResult.mock_for_content(
        "https://www.googleapis.com/youtube/v3/videos",
        200,
        json.dumps(api_resp),
    )
    mock_future = InstantFuture(mock_urlfetch_result)

    with patch("google.appengine.ext.ndb.Context.urlfetch", return_value=mock_future):
        result = YouTubeVideoHelper.get_scheduled_start_times(["abc123"]).get_result()
    assert result == {"abc123": "2023-03-16"}


def test_get_scheduled_start_times_success(ndb_context, mock_google_api_secret) -> None:
    api_resp = {
        "items": [
            {
                "id": "abc123",
                "liveStreamingDetails": {
                    "scheduledStartTime": "2023-03-15T18:00:00Z",
                },
            },
            {
                "id": "def456",
                "liveStreamingDetails": {
                    "scheduledStartTime": "2023-03-15T23:00:00Z",
                    "actualStartTime": "2023-03-16T00:05:00Z",
                },
            },
            {
                "id": "ghi789",
                "liveStreamingDetails": {},
            },
        ]
    }
    mock_urlfetch_result = URLFetchResult.mock_for_content(
        "https://www.googleapis.com/youtube/v3/videos",
        200,
        json.dumps(api_resp),
    )
    mock_future = InstantFuture(mock_urlfetch_result)

    with patch("google.appengine.ext.ndb.Context.urlfetch", return_value=mock_future):
        result = YouTubeVideoHelper.get_scheduled_start_times(
            ["abc123", "def456", "ghi789", "missing"]
        ).get_result()

    assert result == {
        "abc123": "2023-03-15",
        "def456": "2023-03-16",
    }


def test_resolve_channel_id_no_secret(ndb_context) -> None:
    result = YouTubeVideoHelper.resolve_channel_id("FIRSTinMichigan").get_result()
    assert result is None


def test_resolve_channel_id_api_error(ndb_context, mock_google_api_secret) -> None:
    mock_urlfetch_result = URLFetchResult.mock_for_content(
        "https://www.googleapis.com/youtube/v3/channels",
        403,
        "{}",
    )
    mock_future = InstantFuture(mock_urlfetch_result)

    with patch("google.appengine.ext.ndb.Context.urlfetch", return_value=mock_future):
        result = YouTubeVideoHelper.resolve_channel_id("FIRSTinMichigan").get_result()
    assert result is None


def test_resolve_channel_id_not_found(ndb_context, mock_google_api_secret) -> None:
    mock_urlfetch_result = URLFetchResult.mock_for_content(
        "https://www.googleapis.com/youtube/v3/channels",
        200,
        '{"items": []}',
    )
    mock_future = InstantFuture(mock_urlfetch_result)

    with patch("google.appengine.ext.ndb.Context.urlfetch", return_value=mock_future):
        result = YouTubeVideoHelper.resolve_channel_id("does-not-exist").get_result()
    assert result is None


def test_resolve_channel_id_success(ndb_context, mock_google_api_secret) -> None:
    api_resp = {
        "items": [
            {
                "id": "UCjX4WSaAFPgM2PYr-6P",
                "snippet": {"title": "FIRST in Michigan"},
            }
        ]
    }
    mock_urlfetch_result = URLFetchResult.mock_for_content(
        "https://www.googleapis.com/youtube/v3/channels",
        200,
        json.dumps(api_resp),
    )
    mock_future = InstantFuture(mock_urlfetch_result)

    with patch("google.appengine.ext.ndb.Context.urlfetch", return_value=mock_future):
        result = YouTubeVideoHelper.resolve_channel_id("@FIRSTinMichigan").get_result()
    assert result == YouTubeChannel(
        channel_id="UCjX4WSaAFPgM2PYr-6P",
        channel_name="FIRST in Michigan",
    )


def test_resolve_channel_name_wrapper(ndb_context, mock_google_api_secret) -> None:
    api_resp = {
        "items": [
            {
                "id": "UCjX4WSaAFPgM2PYr-6P",
                "snippet": {"title": "FIRST in Michigan"},
            }
        ]
    }
    mock_urlfetch_result = URLFetchResult.mock_for_content(
        "https://www.googleapis.com/youtube/v3/channels",
        200,
        json.dumps(api_resp),
    )
    mock_future = InstantFuture(mock_urlfetch_result)

    with patch("google.appengine.ext.ndb.Context.urlfetch", return_value=mock_future):
        result = YouTubeVideoHelper.resolve_channel_name("FIRSTinMichigan").get_result()

    assert result == YouTubeChannel(
        channel_id="UCjX4WSaAFPgM2PYr-6P",
        channel_name="FIRST in Michigan",
    )


def test_get_playlist_videos_no_secret(ndb_context) -> None:
    with pytest.raises(
        Exception, match="No Google API secret, unable to resolve playlist"
    ):
        YouTubeVideoHelper.videos_in_playlist("playlist").get_result()


def test_get_playlist_videos_unauthorized(ndb_context, mock_google_api_secret) -> None:
    error_resp = {
        "error": {
            "code": 403,
            "message": 'The request cannot be completed because you have exceeded your \u003ca href="/youtube/v3/getting-started#quota"\u003equota\u003c/a\u003e.',
            "errors": [
                {
                    "message": 'The request cannot be completed because you have exceeded your \u003ca href="/youtube/v3/getting-started#quota"\u003equota\u003c/a\u003e.',
                    "domain": "youtube.quota",
                    "reason": "quotaExceeded",
                }
            ],
        }
    }

    mock_urlfetch_result = URLFetchResult.mock_for_content(
        "https://www.googleapis.com/youtube/v3/playlistItems",
        403,
        json.dumps(error_resp),
    )
    mock_future = InstantFuture(mock_urlfetch_result)

    with patch("google.appengine.ext.ndb.Context.urlfetch", return_value=mock_future):
        with pytest.raises(
            Exception, match="Unable to call YouTube API for videos in playlist"
        ):
            YouTubeVideoHelper.videos_in_playlist("playlist_id").get_result()


def test_get_playlist_videos(ndb_context, mock_google_api_secret) -> None:
    with open(
        os.path.join(os.path.dirname(__file__), "data/youtube_playlist_response.json"),
        "r",
    ) as f:
        api_resp = json.load(f)

    mock_urlfetch_result = URLFetchResult.mock_for_content(
        "https://www.googleapis.com/youtube/v3/playlistItems", 200, json.dumps(api_resp)
    )
    mock_future = InstantFuture(mock_urlfetch_result)

    with patch("google.appengine.ext.ndb.Context.urlfetch", return_value=mock_future):
        videos = YouTubeVideoHelper.videos_in_playlist("playlist_id").get_result()
    assert len(videos) == 86
    assert videos[0] == YouTubePlaylistItem(
        video_id="JQcGEsOXNd4",
        video_title="2020ctwat qm1",
        guessed_match_partial="qm1",
    )
    assert videos[85] == YouTubePlaylistItem(
        video_id="TMAY0d6kNLc",
        video_title="frc2020ctwat f1m2",
        guessed_match_partial="f1m2",
    )


def test_get_playlist_videos_paginate(ndb_context, mock_google_api_secret) -> None:
    with open(
        os.path.join(os.path.dirname(__file__), "data/youtube_playlist_response.json"),
        "r",
    ) as f:
        full_api_resp = json.load(f)

    assert len(full_api_resp["items"]) == 86
    resp1 = {
        "items": full_api_resp["items"][:50],
        "nextPageToken": "nextPage",
    }
    resp2 = {
        "items": full_api_resp["items"][50:],
    }

    # Create mock responses for both pages
    mock_urlfetch_result1 = URLFetchResult.mock_for_content(
        "https://www.googleapis.com/youtube/v3/playlistItems", 200, json.dumps(resp1)
    )
    mock_urlfetch_result2 = URLFetchResult.mock_for_content(
        "https://www.googleapis.com/youtube/v3/playlistItems", 200, json.dumps(resp2)
    )

    # Mock urlfetch to return different results on successive calls
    with patch("google.appengine.ext.ndb.Context.urlfetch") as mock_urlfetch:
        mock_urlfetch.side_effect = [
            InstantFuture(mock_urlfetch_result1),
            InstantFuture(mock_urlfetch_result2),
        ]
        videos = YouTubeVideoHelper.videos_in_playlist("playlist_id").get_result()
    assert len(videos) == 86
    assert videos[0] == YouTubePlaylistItem(
        video_id="JQcGEsOXNd4",
        video_title="2020ctwat qm1",
        guessed_match_partial="qm1",
    )
    assert videos[85] == YouTubePlaylistItem(
        video_id="TMAY0d6kNLc",
        video_title="frc2020ctwat f1m2",
        guessed_match_partial="f1m2",
    )


def test_get_upcoming_streams_no_secret(ndb_context) -> None:
    with pytest.raises(
        Exception, match="No Google API secret, unable to fetch upcoming streams"
    ):
        YouTubeVideoHelper.get_upcoming_streams("UC_channel_id").get_result()


def test_get_upcoming_streams_api_error(ndb_context, mock_google_api_secret) -> None:
    mock_urlfetch_result = URLFetchResult.mock_for_content(
        "https://www.googleapis.com/youtube/v3/search",
        403,
        "{}",
    )
    mock_future = InstantFuture(mock_urlfetch_result)

    with patch("google.appengine.ext.ndb.Context.urlfetch", return_value=mock_future):
        with pytest.raises(
            Exception,
            match="Unable to call YouTube API for upcoming streams in channel",
        ):
            YouTubeVideoHelper.get_upcoming_streams("UC_channel_id").get_result()


def test_get_upcoming_streams_empty(ndb_context, mock_google_api_secret) -> None:
    api_resp = {"items": []}
    mock_urlfetch_result = URLFetchResult.mock_for_content(
        "https://www.googleapis.com/youtube/v3/search",
        200,
        json.dumps(api_resp),
    )
    mock_future = InstantFuture(mock_urlfetch_result)

    with patch("google.appengine.ext.ndb.Context.urlfetch", return_value=mock_future):
        streams = YouTubeVideoHelper.get_upcoming_streams("UC_channel_id").get_result()
    assert streams == []


def test_get_upcoming_streams_success(ndb_context, mock_google_api_secret) -> None:
    search_resp = {
        "items": [
            {
                "id": {"videoId": "abc123"},
                "snippet": {
                    "title": "Upcoming Stream 1",
                    "description": "Troy District FIM1",
                },
            },
            {
                "id": {"videoId": "def456"},
                "snippet": {
                    "title": "Upcoming Stream 2",
                },
            },
        ]
    }
    videos_resp = {
        "items": [
            {
                "id": "abc123",
                "liveStreamingDetails": {
                    "scheduledStartTime": "2026-03-15T18:00:00Z",
                },
            },
            {
                "id": "def456",
                "liveStreamingDetails": {
                    "scheduledStartTime": "2026-03-16T19:00:00Z",
                },
            },
        ]
    }

    mock_search_result = URLFetchResult.mock_for_content(
        "https://www.googleapis.com/youtube/v3/search",
        200,
        json.dumps(search_resp),
    )
    mock_videos_result = URLFetchResult.mock_for_content(
        "https://www.googleapis.com/youtube/v3/videos",
        200,
        json.dumps(videos_resp),
    )

    with patch("google.appengine.ext.ndb.Context.urlfetch") as mock_urlfetch:
        mock_urlfetch.side_effect = [
            InstantFuture(mock_search_result),
            InstantFuture(mock_videos_result),
        ]
        streams = YouTubeVideoHelper.get_upcoming_streams("UC_channel_id").get_result()

    assert len(streams) == 2
    assert streams[0] == YouTubeUpcomingStream(
        stream_id="abc123",
        title="Upcoming Stream 1",
        description="Troy District FIM1",
        scheduled_start_time="2026-03-15",
        live_broadcast_content="",
    )
    assert streams[1] == YouTubeUpcomingStream(
        stream_id="def456",
        title="Upcoming Stream 2",
        description="",
        scheduled_start_time="2026-03-16",
        live_broadcast_content="",
    )


def test_get_upcoming_streams_pagination(ndb_context, mock_google_api_secret) -> None:
    search_resp1 = {
        "items": [
            {
                "id": {"videoId": "stream1"},
                "snippet": {
                    "title": "Stream 1",
                },
            }
        ],
        "nextPageToken": "nextPage",
    }
    search_resp2 = {
        "items": [
            {
                "id": {"videoId": "stream2"},
                "snippet": {
                    "title": "Stream 2",
                },
            }
        ],
    }
    videos_resp = {
        "items": [
            {
                "id": "stream1",
                "liveStreamingDetails": {
                    "scheduledStartTime": "2026-03-15T18:00:00Z",
                },
            },
            {
                "id": "stream2",
                "liveStreamingDetails": {
                    "scheduledStartTime": "2026-03-16T19:00:00Z",
                },
            },
        ]
    }

    mock_search_result1 = URLFetchResult.mock_for_content(
        "https://www.googleapis.com/youtube/v3/search",
        200,
        json.dumps(search_resp1),
    )
    mock_search_result2 = URLFetchResult.mock_for_content(
        "https://www.googleapis.com/youtube/v3/search",
        200,
        json.dumps(search_resp2),
    )
    mock_videos_result = URLFetchResult.mock_for_content(
        "https://www.googleapis.com/youtube/v3/videos",
        200,
        json.dumps(videos_resp),
    )

    with patch("google.appengine.ext.ndb.Context.urlfetch") as mock_urlfetch:
        mock_urlfetch.side_effect = [
            InstantFuture(mock_search_result1),
            InstantFuture(mock_search_result2),
            InstantFuture(mock_videos_result),
        ]
        streams = YouTubeVideoHelper.get_upcoming_streams("UC_channel_id").get_result()

    assert len(streams) == 2
    assert streams[0] == YouTubeUpcomingStream(
        stream_id="stream1",
        title="Stream 1",
        description="",
        scheduled_start_time="2026-03-15",
        live_broadcast_content="",
    )
    assert streams[1] == YouTubeUpcomingStream(
        stream_id="stream2",
        title="Stream 2",
        description="",
        scheduled_start_time="2026-03-16",
        live_broadcast_content="",
    )


def test_get_scheduled_start_times_empty(ndb_context) -> None:
    assert YouTubeVideoHelper.get_scheduled_start_times([]).get_result() == {}


def test_get_scheduled_start_times_unexpected_error(ndb_context) -> None:
    with patch.object(
        YouTubeVideoHelper, "get_video_details_batch", side_effect=RuntimeError
    ):
        result = YouTubeVideoHelper.get_scheduled_start_times(["abc123"]).get_result()
    assert result == {}


def test_get_scheduled_start_times_unparseable_times(ndb_context) -> None:
    details = {
        "abc123": {
            "scheduled_start_time": "not-a-date",
            "actual_start_time": "also-not-a-date",
        }
    }
    with patch.object(
        YouTubeVideoHelper,
        "get_video_details_batch",
        return_value=InstantFuture(details),
    ):
        result = YouTubeVideoHelper.get_scheduled_start_times(["abc123"]).get_result()
    # Falls back to the (unparsed) scheduled time
    assert result == {"abc123": "not-a-date"}


def test_get_video_details_batch_empty(ndb_context) -> None:
    assert YouTubeVideoHelper.get_video_details_batch([]).get_result() == {}


def test_resolve_channel_id_blank(ndb_context) -> None:
    assert YouTubeVideoHelper.resolve_channel_id("  @ ").get_result() is None


def _mock_channel_response(api_resp: dict) -> InstantFuture:
    return InstantFuture(
        URLFetchResult.mock_for_content(
            "https://www.googleapis.com/youtube/v3/channels",
            200,
            json.dumps(api_resp),
        )
    )


def test_resolve_channel_id_unusable_items(ndb_context, mock_google_api_secret) -> None:
    # An item without an id or title parses to nothing
    with patch(
        "google.appengine.ext.ndb.Context.urlfetch",
        return_value=_mock_channel_response({"items": [{}]}),
    ):
        result = YouTubeVideoHelper.resolve_channel_id("handle").get_result()
    assert result is None


def test_resolve_channel_id_unexpected_error(
    ndb_context, mock_google_api_secret
) -> None:
    with patch(
        "google.appengine.ext.ndb.Context.urlfetch", side_effect=RuntimeError("boom")
    ):
        result = YouTubeVideoHelper.resolve_channel_id("handle").get_result()
    assert result is None


def test_get_playlist_videos_null_body_and_missing_ids(
    ndb_context, mock_google_api_secret
) -> None:
    page1 = {
        "items": [
            {"id": "item1", "snippet": {"title": "No video id"}},
            {
                "id": "item2",
                "snippet": {"title": "Qual 1", "resourceId": {"videoId": "vid2"}},
            },
        ],
        "nextPageToken": "page2",
    }
    with patch("google.appengine.ext.ndb.Context.urlfetch") as mock_urlfetch:
        mock_urlfetch.side_effect = [
            InstantFuture(
                URLFetchResult.mock_for_content(
                    "https://www.googleapis.com/youtube/v3/playlistItems",
                    200,
                    json.dumps(page1),
                )
            ),
            InstantFuture(
                URLFetchResult.mock_for_content(
                    "https://www.googleapis.com/youtube/v3/playlistItems", 200, "null"
                )
            ),
        ]
        videos = YouTubeVideoHelper.videos_in_playlist("PL_123").get_result()

    assert [v["video_id"] for v in videos] == ["vid2"]


@pytest.mark.parametrize(
    "details_future_kwargs",
    [{"return_value": InstantFuture(None)}, {"side_effect": RuntimeError("boom")}],
)
def test_get_upcoming_streams_details_unavailable(
    ndb_context, mock_google_api_secret, details_future_kwargs: dict
) -> None:
    with (
        patch.object(
            YoutubeUpcomingStreamsDatafeed,
            "fetch_all_pages_async",
            return_value=InstantFuture([{"video_id": "abc123", "title": "Stream"}]),
        ),
        patch.object(
            YoutubeVideoDetailsDatafeed, "fetch_async", **details_future_kwargs
        ),
    ):
        streams = YouTubeVideoHelper.get_upcoming_streams("UC_channel_id").get_result()

    assert streams == []
