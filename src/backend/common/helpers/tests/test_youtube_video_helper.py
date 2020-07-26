from backend.common.helpers.youtube_video_helper import YouTubeVideoHelper


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
