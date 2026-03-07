import json
import os
from unittest.mock import patch

import pytest
from _pytest.monkeypatch import MonkeyPatch

from backend.common.futures import InstantFuture
from backend.common.helpers.youtube_video_helper import (
    YouTubePlaylistItem,
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


def test_get_scheduled_start_time_no_secret(ndb_context) -> None:
    result = YouTubeVideoHelper.get_scheduled_start_time("abc123").get_result()
    assert result is None


def test_get_scheduled_start_time_api_error(
    ndb_context, mock_google_api_secret
) -> None:
    mock_urlfetch_result = URLFetchResult.mock_for_content(
        "https://www.googleapis.com/youtube/v3/videos",
        403,
        "{}",
    )
    mock_future = InstantFuture(mock_urlfetch_result)

    with patch("google.appengine.ext.ndb.Context.urlfetch", return_value=mock_future):
        result = YouTubeVideoHelper.get_scheduled_start_time("abc123").get_result()
    assert result is None


def test_get_scheduled_start_time_no_items(ndb_context, mock_google_api_secret) -> None:
    mock_urlfetch_result = URLFetchResult.mock_for_content(
        "https://www.googleapis.com/youtube/v3/videos",
        200,
        '{"items": []}',
    )
    mock_future = InstantFuture(mock_urlfetch_result)

    with patch("google.appengine.ext.ndb.Context.urlfetch", return_value=mock_future):
        result = YouTubeVideoHelper.get_scheduled_start_time("abc123").get_result()
    assert result is None


def test_get_scheduled_start_time_no_live_details(
    ndb_context, mock_google_api_secret
) -> None:
    mock_urlfetch_result = URLFetchResult.mock_for_content(
        "https://www.googleapis.com/youtube/v3/videos",
        200,
        '{"items": [{}]}',
    )
    mock_future = InstantFuture(mock_urlfetch_result)

    with patch("google.appengine.ext.ndb.Context.urlfetch", return_value=mock_future):
        result = YouTubeVideoHelper.get_scheduled_start_time("abc123").get_result()
    assert result is None


def test_get_scheduled_start_time_no_scheduled_time(
    ndb_context, mock_google_api_secret
) -> None:
    mock_urlfetch_result = URLFetchResult.mock_for_content(
        "https://www.googleapis.com/youtube/v3/videos",
        200,
        '{"items": [{"liveStreamingDetails": {}}]}',
    )
    mock_future = InstantFuture(mock_urlfetch_result)

    with patch("google.appengine.ext.ndb.Context.urlfetch", return_value=mock_future):
        result = YouTubeVideoHelper.get_scheduled_start_time("abc123").get_result()
    assert result is None


def test_get_scheduled_start_time_success(ndb_context, mock_google_api_secret) -> None:
    api_resp = {
        "items": [
            {
                "liveStreamingDetails": {
                    "scheduledStartTime": "2023-03-15T18:00:00Z",
                }
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
        result = YouTubeVideoHelper.get_scheduled_start_time("abc123").get_result()
    assert result == "2023-03-15"


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
        with pytest.raises(Exception, match="Unable to call Youtube API"):
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
