import json
import os
from typing import Dict
from urllib.parse import urlencode

import pytest
import requests
from _pytest.monkeypatch import MonkeyPatch
from requests_mock.mocker import Mocker as RequestsMocker

from backend.common.helpers.youtube_video_helper import (
    YouTubePlaylistItem,
    YouTubeVideoHelper,
)
from backend.common.sitevars.google_api_secret import GoogleApiSecret


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
        ("2020ctwat QF2M3", "qf2m3"),
        ("CTWAT F1M3", "f1m3"),
        ("asdf", ""),
    ],
)
def test_guess_match_partial_from_title(title: str, expected_partial: str) -> None:
    partial = YouTubeVideoHelper.guessMatchPartial(title)
    assert partial == expected_partial


@pytest.fixture
def mock_google_api_secret(monkeypatch: MonkeyPatch) -> None:
    def mock_secret():
        return "google_api_secret"

    monkeypatch.setattr(GoogleApiSecret, "secret_key", mock_secret)


def mock_youtube_api(
    m: RequestsMocker,
    playlist_id: str,
    result: Dict,
    status_code: int = 200,
    next_token: str = "",
) -> None:
    query = {
        "playlistId": playlist_id,
        "pageToken": next_token,
        "key": "google_api_secret",
    }
    m.register_uri(
        "GET",
        f"https://www.googleapis.com/youtube/v3/playlistItems?{urlencode(query)}",
        status_code=status_code,
        json=result,
    )


def test_get_playlist_videos_no_secret(ndb_context) -> None:
    with pytest.raises(
        Exception, match="No Google API secret, unable to resolve playlist"
    ):
        YouTubeVideoHelper.videos_in_playlist("playlist")


def test_get_playlist_videos_unauthorized(
    ndb_context, mock_google_api_secret, requests_mock: RequestsMocker
) -> None:
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

    mock_youtube_api(requests_mock, "playlist_id", error_resp, status_code=403)

    with pytest.raises(requests.exceptions.HTTPError) as exinfo:
        YouTubeVideoHelper.videos_in_playlist("playlist_id")

    assert exinfo.value.response.status_code == 403


def test_get_playlist_videos(
    ndb_context, mock_google_api_secret, requests_mock: RequestsMocker
) -> None:
    with open(
        os.path.join(os.path.dirname(__file__), "data/youtube_playlist_response.json"),
        "r",
    ) as f:
        api_resp = json.load(f)

    mock_youtube_api(requests_mock, "playlist_id", api_resp)

    videos = YouTubeVideoHelper.videos_in_playlist("playlist_id")
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


def test_get_playlist_videos_paginate(
    ndb_context, mock_google_api_secret, requests_mock: RequestsMocker
) -> None:
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
    mock_youtube_api(requests_mock, "playlist_id", resp1, next_token="")
    mock_youtube_api(requests_mock, "playlist_id", resp2, next_token="nextPage")

    videos = YouTubeVideoHelper.videos_in_playlist("playlist_id")
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
