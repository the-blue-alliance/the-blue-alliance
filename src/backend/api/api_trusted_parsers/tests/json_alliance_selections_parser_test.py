import json

import pytest

from backend.api.api_trusted_parsers.json_alliance_selections_parser import (
    JSONAllianceSelectionsParser,
)
from backend.common.datafeed_parsers.exceptions import ParserInputException


def test_parse_single_alliance() -> None:
    data = [["frc254", "frc971", "frc604"]]
    parsed = JSONAllianceSelectionsParser.parse(json.dumps(data))
    assert len(parsed) == 1
    assert parsed[0]["picks"] == ["frc254", "frc971", "frc604"]
    assert parsed[0].get("declines") == []


def test_parse_multiple_alliances() -> None:
    data = [
        ["frc254", "frc971", "frc604"],
        ["frc1678", "frc118", "frc148"],
        ["frc2056", "frc987", "frc1323"],
    ]
    parsed = JSONAllianceSelectionsParser.parse(json.dumps(data))
    assert len(parsed) == 3
    assert parsed[0]["picks"] == ["frc254", "frc971", "frc604"]
    assert parsed[1]["picks"] == ["frc1678", "frc118", "frc148"]
    assert parsed[2]["picks"] == ["frc2056", "frc987", "frc1323"]


def test_parse_eight_alliances() -> None:
    data = [
        ["frc254", "frc971", "frc604"],
        ["frc1678", "frc118", "frc148"],
        ["frc2056", "frc987", "frc1323"],
        ["frc1114", "frc2337", "frc359"],
        ["frc33", "frc67", "frc16"],
        ["frc27", "frc180", "frc195"],
        ["frc225", "frc177", "frc125"],
        ["frc190", "frc175", "frc1991"],
    ]
    parsed = JSONAllianceSelectionsParser.parse(json.dumps(data))
    assert len(parsed) == 8


def test_parse_alliance_with_backup() -> None:
    data = [["frc254", "frc971", "frc604", "frc1678"]]
    parsed = JSONAllianceSelectionsParser.parse(json.dumps(data))
    assert len(parsed) == 1
    assert parsed[0]["picks"] == ["frc254", "frc971", "frc604", "frc1678"]


def test_parse_alliance_with_two_picks() -> None:
    data = [["frc254", "frc971"]]
    parsed = JSONAllianceSelectionsParser.parse(json.dumps(data))
    assert len(parsed) == 1
    assert parsed[0]["picks"] == ["frc254", "frc971"]


def test_parse_bytes_input() -> None:
    data = [["frc254", "frc971", "frc604"]]
    parsed = JSONAllianceSelectionsParser.parse(json.dumps(data).encode("utf-8"))
    assert len(parsed) == 1
    assert parsed[0]["picks"] == ["frc254", "frc971", "frc604"]


def test_parse_empty_list() -> None:
    parsed = JSONAllianceSelectionsParser.parse("[]")
    assert parsed == []


def test_parse_empty_alliance_ignored() -> None:
    data = [["frc254", "frc971", "frc604"], [], ["frc1678", "frc118", "frc148"]]
    parsed = JSONAllianceSelectionsParser.parse(json.dumps(data))
    assert len(parsed) == 2
    assert parsed[0]["picks"] == ["frc254", "frc971", "frc604"]
    assert parsed[1]["picks"] == ["frc1678", "frc118", "frc148"]


def test_bad_team_key_format_raises_exception() -> None:
    data = [["254", "971", "604"]]
    with pytest.raises(ParserInputException, match="Bad team_key"):
        JSONAllianceSelectionsParser.parse(json.dumps(data))


def test_bad_team_key_missing_frc_prefix_raises_exception() -> None:
    data = [["frc254", "971", "frc604"]]
    with pytest.raises(ParserInputException, match="Bad team_key.*971"):
        JSONAllianceSelectionsParser.parse(json.dumps(data))


def test_bad_team_key_with_letters_raises_exception() -> None:
    data = [["frcABC", "frc971", "frc604"]]
    with pytest.raises(ParserInputException, match="Bad team_key.*frcABC"):
        JSONAllianceSelectionsParser.parse(json.dumps(data))


def test_bad_team_key_empty_string_raises_exception() -> None:
    data = [["frc254", "", "frc604"]]
    with pytest.raises(ParserInputException, match="Bad team_key"):
        JSONAllianceSelectionsParser.parse(json.dumps(data))


def test_bad_team_key_in_second_alliance_raises_exception() -> None:
    data = [["frc254", "frc971", "frc604"], ["frc1678", "bad_key", "frc148"]]
    with pytest.raises(ParserInputException, match="Bad team_key.*bad_key"):
        JSONAllianceSelectionsParser.parse(json.dumps(data))


def test_bad_team_key_with_suffix_raises_exception() -> None:
    # Team keys like frc254B are not valid
    data = [["frc254B", "frc971", "frc604"]]
    with pytest.raises(ParserInputException, match="Bad team_key.*frc254B"):
        JSONAllianceSelectionsParser.parse(json.dumps(data))


def test_declines_are_empty() -> None:
    data = [["frc254", "frc971", "frc604"]]
    parsed = JSONAllianceSelectionsParser.parse(json.dumps(data))
    assert parsed[0].get("declines") == []
