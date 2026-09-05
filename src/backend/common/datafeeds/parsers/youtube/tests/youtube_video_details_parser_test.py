from backend.common.datafeeds.parsers.youtube.youtube_video_details_parser import (
    _parse_iso8601_duration,
    YoutubeVideoDetailsParser,
)


def test_parse_iso8601_duration() -> None:
    assert _parse_iso8601_duration("PT3M2S") == 182
    assert _parse_iso8601_duration("PT1H2M30S") == 3750
    assert _parse_iso8601_duration("PT8H") == 28800
    assert _parse_iso8601_duration("P1DT2H") == 93600
    assert _parse_iso8601_duration("PT45S") == 45
    assert _parse_iso8601_duration("") is None
    assert _parse_iso8601_duration("garbage") is None
    assert _parse_iso8601_duration("P") is None


def test_parse_video_details_with_content_details() -> None:
    response = {
        "items": [
            {
                "id": "abc123",
                "snippet": {"title": "2016 F1M1 - NE Championship"},
                "contentDetails": {"duration": "PT3M2S"},
            },
            {
                "id": "def456",
                "snippet": {"title": "Full day stream"},
                "contentDetails": {"duration": "PT8H15M"},
            },
            {
                "id": "nodetails",
                "snippet": {"title": "No content details"},
            },
        ]
    }
    parsed = YoutubeVideoDetailsParser().parse(response)
    assert parsed["abc123"]["title"] == "2016 F1M1 - NE Championship"
    assert parsed["abc123"]["duration_seconds"] == 182
    assert parsed["def456"]["duration_seconds"] == 29700
    assert "duration_seconds" not in parsed["nodetails"]
