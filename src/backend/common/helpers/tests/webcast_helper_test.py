import pytest

from backend.common.consts.webcast_type import WebcastType
from backend.common.frc_api.types import WebcastDetailModelExtV33
from backend.common.helpers.webcast_helper import (
    WebcastParser,
)
from backend.common.models.webcast import Webcast


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
