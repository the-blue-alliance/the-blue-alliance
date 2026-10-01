from typing import Any, Dict, Optional
from unittest.mock import patch

import pytest

from backend.common.consts.event_type import EventType
from backend.common.consts.webcast_type import WebcastType
from backend.common.datafeeds.parsers.youtube.youtube_video_details_parser import (
    ParsedVideoDetails,
)
from backend.common.frc_api.types import WebcastDetailModelExtV33
from backend.common.futures import InstantFuture
from backend.common.helpers.webcast_helper import (
    WebcastParser,
)
from backend.common.models.event import Event
from backend.common.models.webcast import Webcast
from backend.common.urlfetch import URLFetchResult


@pytest.mark.parametrize(
    "url",
    [
        "https://www.youtube.com/watch?v=1v8_2dW7Kik",
        "http://www.youtube.com/watch?v=1v8_2dW7Kik",
        "http://youtu.be/1v8_2dW7Kik",
        "https://youtu.be/1v8_2dW7Kik",
        "https://youtube.com/live/1v8_2dW7Kik",
        "http://youtube.com/live/1v8_2dW7Kik",
        "https://youtube.com/live/1v8_2dW7Kik?si=randomstring",
        "https://www.youtube.com/live/1v8_2dW7Kik?si=randomstring",
        "https://www.youtube.com/watch?v=1v8_2dW7Kik&t=21",
        "https://youtu.be/1v8_2dW7Kik?t=21",
        "https://www.youtube.com/watch?v=1v8_2dW7Kik&feature=youtu.be",
        "https://youtu.be/1v8_2dW7Kik?feature=youtu.be",
        "https://www.youtube.com/watch?v=1v8_2dW7Kik&feature=youtu.be&t=11850",
        "https://youtu.be/1v8_2dW7Kik?feature=youtu.be&t=11850",
        # Bunch of inconsistent (partially outdated) formats
        "https://www.youtube.com/watch?v=1v8_2dW7Kik#t=11850",
        "https://www.youtube.com/watch?v=1v8_2dW7Kik#t=1h",
        "https://youtu.be/1v8_2dW7Kik#t=11850",
        "https://youtu.be/1v8_2dW7Kik#t=1h",
        "https://youtu.be/1v8_2dW7Kik?t=3h17m30s",
        "https://www.youtube.com/watch?v=1v8_2dW7Kik&t=3h17m30s",
    ],
)
def test_youtube_webcast_dict_from_url(url: str) -> None:
    webcast = WebcastParser.webcast_dict_from_url(url).get_result()
    assert webcast is not None and webcast["channel"] == "1v8_2dW7Kik"


def test_frc_api_twitch_webcast() -> None:
    api_webcast = WebcastDetailModelExtV33(
        link="https://www.twitch.tv/firstinspires12",
        provider="Twitch",
        channel="firstinspires12",
        slug=None,
        isFirstWebcastUnit=True,
        date=None,
    )
    webcast = WebcastParser.webcast_dict_from_api_response(api_webcast)
    assert webcast == Webcast(
        type=WebcastType.TWITCH,
        channel="firstinspires12",
    )


def test_frc_api_youtube_webcast() -> None:
    api_webcast = WebcastDetailModelExtV33(
        link="https://www.youtube.com/watch?v=eUdvSJ-mqtU",
        provider="Youtube",
        channel="FIRSTRoboticsCompetition",
        slug="1v8_2dW7Kik",
        isFirstWebcastUnit=True,
        date="2026-01-01",
    )
    webcast = WebcastParser.webcast_dict_from_api_response(api_webcast)
    assert webcast == Webcast(
        type=WebcastType.YOUTUBE,
        channel="1v8_2dW7Kik",
        date="2026-01-01",
    )


@pytest.mark.parametrize(
    "short_name, event_short, video, expected",
    [
        ("New York City", "nyny", {"title": "New York City Regional"}, True),
        (
            "New York City",
            "nyny",
            {"title": "FRC Live", "description": "Watch New York City here"},
            True,
        ),
        ("New York City", "nyny", {"title": "FRC Live", "description": "NYNY"}, True),
        ("New York City", "nyny", {"title": "FRC Live", "description": "nyny"}, False),
        ("New York City", "nyny", {"title": "Hudson Valley"}, False),
        (None, "nyny", {"title": "New York City", "description": "NYNY"}, True),
        (None, "nyny", {"title": "New York City"}, False),
        (None, None, {"title": "New York City", "description": "NYNY"}, False),
    ],
)
def test_stream_matches_event(
    short_name: Optional[str],
    event_short: Optional[str],
    video: Dict[str, str],
    expected: bool,
) -> None:
    event = Event(
        id="2026nyny",
        year=2026,
        short_name=short_name,
        event_short=event_short,
        event_type_enum=EventType.REGIONAL,
    )
    video_details = ParsedVideoDetails(video_id="abc", **video)  # pyre-ignore[6]

    assert WebcastParser.stream_matches_event(video_details, event) is expected


def test_frc_api_unknown_provider_webcast() -> None:
    api_webcast = WebcastDetailModelExtV33(
        link="https://example.com/stream",
        provider="Vimeo",
        channel="firstinspires",
        slug=None,
        isFirstWebcastUnit=True,
        date=None,
    )

    assert WebcastParser.webcast_dict_from_api_response(api_webcast) is None


def test_frc_api_webcast_missing_channel() -> None:
    api_webcast = WebcastDetailModelExtV33(
        link="https://www.youtube.com/watch?v=eUdvSJ-mqtU",
        provider="Youtube",
        channel="FIRSTRoboticsCompetition",
        slug=None,
        isFirstWebcastUnit=True,
        date=None,
    )

    assert WebcastParser.webcast_dict_from_api_response(api_webcast) is None


@pytest.mark.parametrize(
    "url, expected",
    [
        (
            "https://www.twitch.tv/firstinspires",
            Webcast(type=WebcastType.TWITCH, channel="firstinspires"),
        ),
        (
            "twitch.tv/first_inspires?foo=bar",
            Webcast(type=WebcastType.TWITCH, channel="first_inspires"),
        ),
        ("https://www.twitch.tv/", None),
        ("https://www.youtube.com/", None),
        ("https://www.youtube.com/watch?v=", None),
        ("https://example.com/watch", None),
    ],
)
def test_webcast_dict_from_url_without_fetching(
    url: str, expected: Optional[Webcast]
) -> None:
    assert WebcastParser.webcast_dict_from_url(url).get_result() == expected


def _mock_urlfetch(url: str, status_code: int, content: str) -> Any:
    return patch(
        "google.appengine.ext.ndb.Context.urlfetch",
        return_value=InstantFuture(
            URLFetchResult.mock_for_content(url, status_code, content)
        ),
    )


USTREAM_URL = "http://www.ustream.tv/channel/first-nyc"
LIVESTREAM_URL = "https://livestream.com/accounts/1234/events/5678"


@pytest.mark.parametrize(
    "status_code, html, expected",
    [
        (
            200,
            '<html><head><meta name="ustream:channel_id" content="17439314"></head></html>',
            Webcast(type=WebcastType.USTREAM, channel="17439314"),
        ),
        (
            200,
            '<html><head><meta name="ustream:channel_id" content=""></head></html>',
            None,
        ),
        (200, "<html><head><title>Ustream</title></head></html>", None),
        (404, "", None),
    ],
)
def test_webcast_dict_from_ustream_url(
    status_code: int, html: str, expected: Optional[Webcast]
) -> None:
    with _mock_urlfetch(USTREAM_URL, status_code, html) as mock_fetch:
        webcast = WebcastParser.webcast_dict_from_url(USTREAM_URL).get_result()

    assert webcast == expected
    mock_fetch.assert_called_once_with(USTREAM_URL, deadline=10)


@pytest.mark.parametrize(
    "status_code, html, expected",
    [
        (
            200,
            '<html><head><meta name="twitter:player" '
            'content="https://livestream.com/accounts/1234/events/5678/player"></head></html>',
            Webcast(type=WebcastType.LIVESTREAM, channel="1234", file="5678"),
        ),
        (
            200,
            '<html><head><meta name="twitter:player" content="https://example.com/player"></head></html>',
            None,
        ),
        (200, "<html><head><title>Livestream</title></head></html>", None),
        (500, "", None),
    ],
)
def test_webcast_dict_from_livestream_url(
    status_code: int, html: str, expected: Optional[Webcast]
) -> None:
    with _mock_urlfetch(LIVESTREAM_URL, status_code, html) as mock_fetch:
        webcast = WebcastParser.webcast_dict_from_url(LIVESTREAM_URL).get_result()

    assert webcast == expected
    mock_fetch.assert_called_once_with(LIVESTREAM_URL, deadline=10)
