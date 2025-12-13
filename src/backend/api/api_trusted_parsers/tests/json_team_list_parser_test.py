import json

import pytest

from backend.api.api_trusted_parsers.json_team_list_parser import JSONTeamListParser
from backend.common.datafeed_parsers.exceptions import ParserInputException


def test_parse_single_team_key() -> None:
    data = ["frc254"]
    parsed = JSONTeamListParser.parse(json.dumps(data))
    assert parsed == ["frc254"]


def test_parse_multiple_team_keys() -> None:
    data = ["frc254", "frc971", "frc1678"]
    parsed = JSONTeamListParser.parse(json.dumps(data))
    assert parsed == ["frc254", "frc971", "frc1678"]


def test_parse_empty_list() -> None:
    data: list[str] = []
    parsed = JSONTeamListParser.parse(json.dumps(data))
    assert parsed == []


def test_parse_bytes_input() -> None:
    data = ["frc254", "frc971"]
    parsed = JSONTeamListParser.parse(json.dumps(data).encode("utf-8"))
    assert parsed == ["frc254", "frc971"]


def test_parse_invalid_team_key_missing_prefix() -> None:
    data = ["254"]
    with pytest.raises(ParserInputException, match="Invalid team keys provided"):
        JSONTeamListParser.parse(json.dumps(data))


def test_parse_invalid_team_key_with_letters() -> None:
    data = ["frcABC"]
    with pytest.raises(ParserInputException, match="Invalid team keys provided"):
        JSONTeamListParser.parse(json.dumps(data))


def test_parse_invalid_team_key_wrong_prefix() -> None:
    data = ["ftc254"]
    with pytest.raises(ParserInputException, match="Invalid team keys provided"):
        JSONTeamListParser.parse(json.dumps(data))


def test_parse_multiple_invalid_team_keys() -> None:
    data = ["254", "frcABC", "frc971"]
    with pytest.raises(ParserInputException, match="Invalid team keys provided"):
        JSONTeamListParser.parse(json.dumps(data))


def test_parse_mixed_valid_and_invalid_team_keys() -> None:
    data = ["frc254", "invalid", "frc971"]
    with pytest.raises(ParserInputException, match="Invalid team keys provided"):
        JSONTeamListParser.parse(json.dumps(data))
