import json

import pytest

from backend.api.api_trusted_parsers.json_match_video_parser import (
    JSONMatchVideoParser,
)
from backend.common.datafeed_parsers.exceptions import ParserInputException


def test_parse_empty_dict() -> None:
    parsed = JSONMatchVideoParser.parse("2024casj", "{}")
    assert parsed == {}


def test_parse_bytes_input() -> None:
    data = {"qm1": "dQw4w9WgXcw"}
    parsed = JSONMatchVideoParser.parse("2024casj", json.dumps(data).encode("utf-8"))
    assert parsed == {"2024casj_qm1": "dQw4w9WgXcw"}


def test_parse_single_qual_match() -> None:
    data = {"qm1": "dQw4w9WgXcw"}
    parsed = JSONMatchVideoParser.parse("2024casj", json.dumps(data))
    assert parsed == {"2024casj_qm1": "dQw4w9WgXcw"}


def test_parse_multiple_qual_matches() -> None:
    data = {"qm1": "dQw4w9WgXcw", "qm2": "oHg5SJYRHA0", "qm10": "abc12345678"}
    parsed = JSONMatchVideoParser.parse("2024casj", json.dumps(data))
    assert parsed == {
        "2024casj_qm1": "dQw4w9WgXcw",
        "2024casj_qm2": "oHg5SJYRHA0",
        "2024casj_qm10": "abc12345678",
    }


def test_parse_quarterfinal_match() -> None:
    data = {"qf1m1": "dQw4w9WgXcw"}
    parsed = JSONMatchVideoParser.parse("2024casj", json.dumps(data))
    assert parsed == {"2024casj_qf1m1": "dQw4w9WgXcw"}


def test_parse_semifinal_match() -> None:
    data = {"sf2m1": "dQw4w9WgXcw"}
    parsed = JSONMatchVideoParser.parse("2024casj", json.dumps(data))
    assert parsed == {"2024casj_sf2m1": "dQw4w9WgXcw"}


def test_parse_final_match() -> None:
    data = {"f1m1": "dQw4w9WgXcw"}
    parsed = JSONMatchVideoParser.parse("2024casj", json.dumps(data))
    assert parsed == {"2024casj_f1m1": "dQw4w9WgXcw"}


def test_parse_eighth_final_match() -> None:
    data = {"ef1m1": "dQw4w9WgXcw"}
    parsed = JSONMatchVideoParser.parse("2024casj", json.dumps(data))
    assert parsed == {"2024casj_ef1m1": "dQw4w9WgXcw"}


def test_parse_mixed_comp_levels() -> None:
    data = {
        "qm5": "dQw4w9WgXcw",
        "qf1m1": "oHg5SJYRHA0",
        "sf1m2": "abc12345678",
        "f1m1": "xyz98765432",
    }
    parsed = JSONMatchVideoParser.parse("2024casj", json.dumps(data))
    assert parsed == {
        "2024casj_qm5": "dQw4w9WgXcw",
        "2024casj_qf1m1": "oHg5SJYRHA0",
        "2024casj_sf1m2": "abc12345678",
        "2024casj_f1m1": "xyz98765432",
    }


def test_parse_event_with_number() -> None:
    data = {"qm1": "dQw4w9WgXcw"}
    parsed = JSONMatchVideoParser.parse("2024iscmp2", json.dumps(data))
    assert parsed == {"2024iscmp2_qm1": "dQw4w9WgXcw"}


def test_parse_invalid_match_id_raises_exception() -> None:
    data = {"invalid": "abc123"}
    with pytest.raises(ParserInputException, match="Invalid match IDs provided"):
        JSONMatchVideoParser.parse("2024casj", json.dumps(data))


def test_parse_invalid_match_id_bad_comp_level_raises_exception() -> None:
    data = {"xf1m1": "abc123"}
    with pytest.raises(ParserInputException, match="Invalid match IDs provided"):
        JSONMatchVideoParser.parse("2024casj", json.dumps(data))


def test_parse_invalid_match_id_missing_match_number_raises_exception() -> None:
    data = {"qm": "abc123"}
    with pytest.raises(ParserInputException, match="Invalid match IDs provided"):
        JSONMatchVideoParser.parse("2024casj", json.dumps(data))


def test_parse_multiple_invalid_match_ids_raises_exception() -> None:
    data = {"invalid1": "abc123", "invalid2": "def456"}
    with pytest.raises(ParserInputException, match="Invalid match IDs provided"):
        JSONMatchVideoParser.parse("2024casj", json.dumps(data))


def test_parse_mixed_valid_and_invalid_raises_exception() -> None:
    data = {"qm1": "abc123", "invalid": "def456"}
    with pytest.raises(ParserInputException, match="Invalid match IDs provided"):
        JSONMatchVideoParser.parse("2024casj", json.dumps(data))


def test_parse_full_match_key_instead_of_partial_raises_exception() -> None:
    # User should provide match partial (e.g., "qm1"), not full key
    data = {"2024casj_qm1": "dQw4w9WgXcw"}
    with pytest.raises(ParserInputException, match="Invalid match IDs provided"):
        JSONMatchVideoParser.parse("2024casj", json.dumps(data))


def test_parse_invalid_video_id_too_short_raises_exception() -> None:
    data = {"qm1": "abc123"}
    with pytest.raises(
        ParserInputException, match="Invalid YouTube video IDs provided"
    ):
        JSONMatchVideoParser.parse("2024casj", json.dumps(data))


def test_parse_invalid_video_id_too_long_raises_exception() -> None:
    data = {"qm1": "abc1234567890"}
    with pytest.raises(
        ParserInputException, match="Invalid YouTube video IDs provided"
    ):
        JSONMatchVideoParser.parse("2024casj", json.dumps(data))


def test_parse_invalid_video_id_bad_chars_raises_exception() -> None:
    data = {"qm1": "abc!@#$%^&*("}
    with pytest.raises(
        ParserInputException, match="Invalid YouTube video IDs provided"
    ):
        JSONMatchVideoParser.parse("2024casj", json.dumps(data))


def test_parse_multiple_invalid_video_ids_raises_exception() -> None:
    data = {"qm1": "tooshort", "qm2": "also_short"}
    with pytest.raises(
        ParserInputException, match="Invalid YouTube video IDs provided"
    ):
        JSONMatchVideoParser.parse("2024casj", json.dumps(data))


def test_parse_valid_video_id_with_hyphens_and_underscores() -> None:
    data = {"qm1": "abc-def_123"}
    parsed = JSONMatchVideoParser.parse("2024casj", json.dumps(data))
    assert parsed == {"2024casj_qm1": "abc-def_123"}
