import json

import pytest

from backend.api.api_trusted_parsers.json_webcast_update_parser import (
    JSONWebcastUpdateParser,
)
from backend.common.consts.webcast_type import WebcastType
from backend.common.datafeed_parsers.exceptions import ParserInputException


def test_parse_empty_dict() -> None:
    parsed = JSONWebcastUpdateParser.parse("{}")
    assert parsed == {}


def test_parse_empty_webcast_list() -> None:
    parsed = JSONWebcastUpdateParser.parse(json.dumps({"webcasts": []}))
    assert parsed == {}


def test_parse_webcasts_not_a_list() -> None:
    with pytest.raises(ParserInputException, match="webcasts must be a list"):
        JSONWebcastUpdateParser.parse(json.dumps({"webcasts": {"type": "twitch"}}))


def test_parse_type_and_channel() -> None:
    data = {"webcasts": [{"type": "twitch", "channel": "firstinspires"}]}
    parsed = JSONWebcastUpdateParser.parse(json.dumps(data))
    assert parsed == {
        "webcasts": [{"type": WebcastType.TWITCH, "channel": "firstinspires"}]
    }


def test_parse_bytes_input() -> None:
    data = {"webcasts": [{"type": "youtube", "channel": "abc123"}]}
    parsed = JSONWebcastUpdateParser.parse(json.dumps(data).encode("utf-8"))
    assert parsed == {"webcasts": [{"type": WebcastType.YOUTUBE, "channel": "abc123"}]}


def test_parse_from_url(ndb_stub) -> None:
    data = {"webcasts": [{"url": "https://www.youtube.com/watch?v=abc123xyz"}]}
    parsed = JSONWebcastUpdateParser.parse(json.dumps(data))
    assert parsed == {
        "webcasts": [{"type": WebcastType.YOUTUBE, "channel": "abc123xyz"}]
    }


def test_parse_from_unknown_url(ndb_stub) -> None:
    data = {"webcasts": [{"url": "https://example.com/not-a-webcast"}]}
    with pytest.raises(ParserInputException, match="Unknown webcast url"):
        JSONWebcastUpdateParser.parse(json.dumps(data))


@pytest.mark.parametrize(
    "webcast",
    [
        {},
        {"type": "twitch"},
        {"channel": "firstinspires"},
        {"type": "twitch", "channel": ""},
        {"file": "abc"},
    ],
)
def test_parse_invalid_webcast(webcast: dict[str, str]) -> None:
    with pytest.raises(ParserInputException, match="Invalid webcast"):
        JSONWebcastUpdateParser.parse(json.dumps({"webcasts": [webcast]}))


def test_parse_with_file() -> None:
    data = {"webcasts": [{"type": "youtube", "channel": "abc123", "file": "some_file"}]}
    parsed = JSONWebcastUpdateParser.parse(json.dumps(data))
    assert parsed == {
        "webcasts": [
            {"type": WebcastType.YOUTUBE, "channel": "abc123", "file": "some_file"}
        ]
    }


def test_parse_with_date() -> None:
    data = {"webcasts": [{"type": "twitch", "channel": "abc123", "date": "2024-03-14"}]}
    parsed = JSONWebcastUpdateParser.parse(json.dumps(data))
    assert parsed == {
        "webcasts": [
            {"type": WebcastType.TWITCH, "channel": "abc123", "date": "2024-03-14"}
        ]
    }


@pytest.mark.parametrize("date", ["03/14/2024", "2024-13-01", "tomorrow"])
def test_parse_with_invalid_date(date: str) -> None:
    data = {"webcasts": [{"type": "twitch", "channel": "abc123", "date": date}]}
    with pytest.raises(ParserInputException, match="Invalid webcast date"):
        JSONWebcastUpdateParser.parse(json.dumps(data))


def test_parse_url_with_file_and_date(ndb_stub) -> None:
    data = {
        "webcasts": [
            {
                "url": "https://twitch.tv/firstinspires",
                "file": "day1",
                "date": "2024-03-14",
            }
        ]
    }
    parsed = JSONWebcastUpdateParser.parse(json.dumps(data))
    assert parsed == {
        "webcasts": [
            {
                "type": WebcastType.TWITCH,
                "channel": "firstinspires",
                "file": "day1",
                "date": "2024-03-14",
            }
        ]
    }
