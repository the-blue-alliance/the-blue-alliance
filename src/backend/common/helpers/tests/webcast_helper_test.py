import pytest

from backend.common.helpers.webcast_helper import (
    WebcastParser,
)

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
        "https://www.youtube.com/watch?v=1v8_2dW7Kik&t=3h17m30s"
    ],
)
def test_youtube_webcast_dict_from_url(url: str) -> None:
    parser = WebcastParser()
    assert (
        parser.webcast_dict_from_url(url).channel
        == "1v8_2dW7Kik"
    )
