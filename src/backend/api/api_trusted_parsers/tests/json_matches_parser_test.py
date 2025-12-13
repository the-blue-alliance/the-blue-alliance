import json
from typing import Any

import pytest
from pyre_extensions import none_throws
from pyre_extensions.safe_json import InvalidJson

from backend.api.api_trusted_parsers.json_matches_parser import JSONMatchesParser
from backend.common.consts.alliance_color import AllianceColor
from backend.common.datafeed_parsers.exceptions import ParserInputException


def make_match(overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    """Helper to create a valid match dict with optional overrides."""
    match: dict[str, Any] = {
        "comp_level": "qm",
        "set_number": 1,
        "match_number": 1,
        "alliances": {
            "red": {"teams": ["frc254", "frc971", "frc1678"], "score": 100},
            "blue": {"teams": ["frc604", "frc1323", "frc973"], "score": 90},
        },
    }
    if overrides:
        match.update(overrides)
    return match


# Basic parsing tests
def test_parse_single_qual_match() -> None:
    data = [make_match()]
    parsed = JSONMatchesParser.parse(json.dumps(data), 2024)
    assert len(parsed) == 1
    match = parsed[0]
    assert match["comp_level"] == "qm"
    assert match["set_number"] == 1
    assert match["match_number"] == 1
    assert "frc254" in match["team_key_names"]
    assert "frc604" in match["team_key_names"]


def test_parse_multiple_matches() -> None:
    data = [
        make_match({"match_number": 1}),
        make_match({"match_number": 2}),
        make_match({"match_number": 3}),
    ]
    parsed = JSONMatchesParser.parse(json.dumps(data), 2024)
    assert len(parsed) == 3
    assert parsed[0]["match_number"] == 1
    assert parsed[1]["match_number"] == 2
    assert parsed[2]["match_number"] == 3


def test_parse_bytes_input() -> None:
    data = [make_match()]
    parsed = JSONMatchesParser.parse(json.dumps(data).encode("utf-8"), 2024)
    assert len(parsed) == 1
    assert parsed[0]["comp_level"] == "qm"


def test_parse_empty_list() -> None:
    parsed = JSONMatchesParser.parse("[]", 2024)
    assert parsed == []


# Comp level tests
def test_parse_qm_comp_level() -> None:
    data = [make_match({"comp_level": "qm"})]
    parsed = JSONMatchesParser.parse(json.dumps(data), 2024)
    assert parsed[0]["comp_level"] == "qm"


def test_parse_ef_comp_level() -> None:
    data = [make_match({"comp_level": "ef", "set_number": 1})]
    parsed = JSONMatchesParser.parse(json.dumps(data), 2024)
    assert parsed[0]["comp_level"] == "ef"
    assert parsed[0]["set_number"] == 1


def test_parse_qf_comp_level() -> None:
    data = [make_match({"comp_level": "qf", "set_number": 2})]
    parsed = JSONMatchesParser.parse(json.dumps(data), 2024)
    assert parsed[0]["comp_level"] == "qf"
    assert parsed[0]["set_number"] == 2


def test_parse_sf_comp_level() -> None:
    data = [make_match({"comp_level": "sf", "set_number": 1})]
    parsed = JSONMatchesParser.parse(json.dumps(data), 2024)
    assert parsed[0]["comp_level"] == "sf"
    assert parsed[0]["set_number"] == 1


def test_parse_f_comp_level() -> None:
    data = [make_match({"comp_level": "f", "set_number": 1})]
    parsed = JSONMatchesParser.parse(json.dumps(data), 2024)
    assert parsed[0]["comp_level"] == "f"
    assert parsed[0]["set_number"] == 1


def test_parse_qm_ignores_set_number() -> None:
    """For qual matches, set_number should be set to 1 regardless of input."""
    data = [make_match({"comp_level": "qm", "set_number": 99})]
    parsed = JSONMatchesParser.parse(json.dumps(data), 2024)
    assert parsed[0]["set_number"] == 1


def test_missing_comp_level_raises_exception() -> None:
    match = make_match()
    del match["comp_level"]
    with pytest.raises(ParserInputException, match="comp_level"):
        JSONMatchesParser.parse(json.dumps([match]), 2024)


def test_invalid_comp_level_raises_exception() -> None:
    data = [make_match({"comp_level": "invalid"})]
    with pytest.raises(ParserInputException, match="comp_level"):
        JSONMatchesParser.parse(json.dumps(data), 2024)


# Set number tests
def test_playoff_match_missing_set_number_raises_exception() -> None:
    match = make_match({"comp_level": "qf"})
    del match["set_number"]
    with pytest.raises(ParserInputException, match="set_number"):
        JSONMatchesParser.parse(json.dumps([match]), 2024)


def test_playoff_match_non_integer_set_number_raises_exception() -> None:
    data = [make_match({"comp_level": "qf", "set_number": "1"})]
    with pytest.raises(ParserInputException, match="set_number"):
        JSONMatchesParser.parse(json.dumps(data), 2024)


# Match number tests
def test_missing_match_number_raises_exception() -> None:
    match = make_match()
    del match["match_number"]
    with pytest.raises(ParserInputException, match="match_number"):
        JSONMatchesParser.parse(json.dumps([match]), 2024)


def test_non_integer_match_number_raises_exception() -> None:
    data = [make_match({"match_number": "1"})]
    with pytest.raises(ParserInputException, match="match_number"):
        JSONMatchesParser.parse(json.dumps(data), 2024)


# Alliance tests
def test_missing_alliances_raises_exception() -> None:
    match = make_match()
    del match["alliances"]
    with pytest.raises(ParserInputException, match="alliances"):
        JSONMatchesParser.parse(json.dumps([match]), 2024)


def test_alliances_not_dict_raises_exception() -> None:
    data = [make_match({"alliances": "not a dict"})]
    with pytest.raises(ParserInputException, match="alliances"):
        JSONMatchesParser.parse(json.dumps(data), 2024)


def test_invalid_alliance_color_raises_exception() -> None:
    data = [
        make_match(
            {
                "alliances": {
                    "red": {"teams": ["frc254"], "score": 100},
                    "green": {"teams": ["frc604"], "score": 90},
                }
            }
        )
    ]
    with pytest.raises(ParserInputException, match="Alliance color"):
        JSONMatchesParser.parse(json.dumps(data), 2024)


def test_missing_teams_in_alliance_raises_exception() -> None:
    data = [
        make_match(
            {
                "alliances": {
                    "red": {"score": 100},
                    "blue": {"teams": ["frc604"], "score": 90},
                }
            }
        )
    ]
    with pytest.raises(ParserInputException, match="teams"):
        JSONMatchesParser.parse(json.dumps(data), 2024)


def test_missing_score_in_alliance_raises_exception() -> None:
    data = [
        make_match(
            {
                "alliances": {
                    "red": {"teams": ["frc254"]},
                    "blue": {"teams": ["frc604"], "score": 90},
                }
            }
        )
    ]
    with pytest.raises(ParserInputException, match="score"):
        JSONMatchesParser.parse(json.dumps(data), 2024)


def test_invalid_team_key_raises_exception() -> None:
    data = [
        make_match(
            {
                "alliances": {
                    "red": {"teams": ["254"], "score": 100},
                    "blue": {"teams": ["frc604"], "score": 90},
                }
            }
        )
    ]
    with pytest.raises(ParserInputException, match="Bad team"):
        JSONMatchesParser.parse(json.dumps(data), 2024)


def test_invalid_team_key_letters_raises_exception() -> None:
    data = [
        make_match(
            {
                "alliances": {
                    "red": {"teams": ["frcABC"], "score": 100},
                    "blue": {"teams": ["frc604"], "score": 90},
                }
            }
        )
    ]
    with pytest.raises(ParserInputException, match="Bad team"):
        JSONMatchesParser.parse(json.dumps(data), 2024)


def test_null_score_is_valid() -> None:
    data = [
        make_match(
            {
                "alliances": {
                    "red": {"teams": ["frc254"], "score": None},
                    "blue": {"teams": ["frc604"], "score": None},
                }
            }
        )
    ]
    parsed = JSONMatchesParser.parse(json.dumps(data), 2024)
    alliances = json.loads(parsed[0]["alliances_json"])
    assert alliances[AllianceColor.RED]["score"] is None
    assert alliances[AllianceColor.BLUE]["score"] is None


def test_non_integer_score_raises_exception() -> None:
    data = [
        make_match(
            {
                "alliances": {
                    "red": {"teams": ["frc254"], "score": "100"},
                    "blue": {"teams": ["frc604"], "score": 90},
                }
            }
        )
    ]
    with pytest.raises(ParserInputException, match="score"):
        JSONMatchesParser.parse(json.dumps(data), 2024)


# Surrogate teams tests
def test_parse_surrogates() -> None:
    data = [
        make_match(
            {
                "alliances": {
                    "red": {
                        "teams": ["frc254", "frc971", "frc1678"],
                        "score": 100,
                        "surrogates": ["frc254"],
                    },
                    "blue": {"teams": ["frc604"], "score": 90},
                }
            }
        )
    ]
    parsed = JSONMatchesParser.parse(json.dumps(data), 2024)
    alliances = json.loads(parsed[0]["alliances_json"])
    assert alliances[AllianceColor.RED]["surrogates"] == ["frc254"]


def test_invalid_surrogate_team_key_raises_exception() -> None:
    data = [
        make_match(
            {
                "alliances": {
                    "red": {
                        "teams": ["frc254"],
                        "score": 100,
                        "surrogates": ["254"],
                    },
                    "blue": {"teams": ["frc604"], "score": 90},
                }
            }
        )
    ]
    with pytest.raises(ParserInputException, match="Bad surrogate team"):
        JSONMatchesParser.parse(json.dumps(data), 2024)


def test_surrogate_not_in_teams_raises_exception() -> None:
    data = [
        make_match(
            {
                "alliances": {
                    "red": {
                        "teams": ["frc254"],
                        "score": 100,
                        "surrogates": ["frc999"],
                    },
                    "blue": {"teams": ["frc604"], "score": 90},
                }
            }
        )
    ]
    with pytest.raises(ParserInputException, match="Bad surrogate team"):
        JSONMatchesParser.parse(json.dumps(data), 2024)


# DQ teams tests
def test_parse_dqs() -> None:
    data = [
        make_match(
            {
                "alliances": {
                    "red": {
                        "teams": ["frc254", "frc971"],
                        "score": 100,
                        "dqs": ["frc971"],
                    },
                    "blue": {"teams": ["frc604"], "score": 90},
                }
            }
        )
    ]
    parsed = JSONMatchesParser.parse(json.dumps(data), 2024)
    alliances = json.loads(parsed[0]["alliances_json"])
    assert alliances[AllianceColor.RED]["dqs"] == ["frc971"]


def test_invalid_dq_team_key_raises_exception() -> None:
    data = [
        make_match(
            {
                "alliances": {
                    "red": {"teams": ["frc254"], "score": 100, "dqs": ["254"]},
                    "blue": {"teams": ["frc604"], "score": 90},
                }
            }
        )
    ]
    with pytest.raises(ParserInputException, match="Bad dq team"):
        JSONMatchesParser.parse(json.dumps(data), 2024)


def test_dq_not_in_teams_raises_exception() -> None:
    data = [
        make_match(
            {
                "alliances": {
                    "red": {"teams": ["frc254"], "score": 100, "dqs": ["frc999"]},
                    "blue": {"teams": ["frc604"], "score": 90},
                }
            }
        )
    ]
    with pytest.raises(ParserInputException, match="Bad dq team"):
        JSONMatchesParser.parse(json.dumps(data), 2024)


# Score breakdown tests
def test_parse_score_breakdown() -> None:
    data = [
        make_match(
            {
                "score_breakdown": {
                    "red": {"totalPoints": 100, "autoPoints": 20},
                    "blue": {"totalPoints": 90, "autoPoints": 15},
                }
            }
        )
    ]
    parsed = JSONMatchesParser.parse(json.dumps(data), 2024)
    breakdown = json.loads(parsed[0]["score_breakdown_json"])  # type: ignore[arg-type]
    assert breakdown["red"]["totalPoints"] == 100
    assert breakdown["blue"]["autoPoints"] == 15


def test_score_breakdown_null_is_valid() -> None:
    data = [make_match({"score_breakdown": None})]
    parsed = JSONMatchesParser.parse(json.dumps(data), 2024)
    assert parsed[0]["score_breakdown_json"] is None


def test_score_breakdown_not_dict_raises_exception() -> None:
    data = [make_match({"score_breakdown": "not a dict"})]
    with pytest.raises(ParserInputException, match="score_breakdown"):
        JSONMatchesParser.parse(json.dumps(data), 2024)


def test_score_breakdown_invalid_color_raises_exception() -> None:
    data = [make_match({"score_breakdown": {"red": {}, "green": {}}})]
    with pytest.raises(ParserInputException, match="Alliance color"):
        JSONMatchesParser.parse(json.dumps(data), 2024)


def test_score_breakdown_invalid_key_raises_exception() -> None:
    data = [
        make_match(
            {
                "score_breakdown": {
                    "red": {"invalidKey": 100},
                    "blue": {"totalPoints": 90},
                }
            }
        )
    ]
    with pytest.raises(ParserInputException, match="Invalid score breakdown fields"):
        JSONMatchesParser.parse(json.dumps(data), 2024)


def test_score_breakdown_valid_keys_for_year() -> None:
    # Test with 2024-specific keys
    data = [
        make_match(
            {
                "score_breakdown": {
                    "red": {"autoPoints": 20, "teleopPoints": 50, "totalPoints": 100},
                    "blue": {"autoPoints": 15, "teleopPoints": 45, "totalPoints": 90},
                }
            }
        )
    ]
    parsed = JSONMatchesParser.parse(json.dumps(data), 2024)
    assert parsed[0]["score_breakdown_json"] is not None


def test_score_breakdown_2025_keys() -> None:
    # Test with 2025-specific keys
    data = [
        make_match(
            {
                "score_breakdown": {
                    "red": {"autoPoints": 20, "algaePoints": 10, "totalPoints": 100},
                    "blue": {"autoPoints": 15, "algaePoints": 5, "totalPoints": 90},
                }
            }
        )
    ]
    parsed = JSONMatchesParser.parse(json.dumps(data), 2025)
    assert parsed[0]["score_breakdown_json"] is not None


def test_score_breakdown_wrong_year_key_raises_exception() -> None:
    # algaePoints is a 2025 key, not valid for 2024
    data = [
        make_match(
            {
                "score_breakdown": {
                    "red": {"algaePoints": 10},
                    "blue": {"algaePoints": 5},
                }
            }
        )
    ]
    with pytest.raises(ParserInputException, match="Invalid score breakdown fields"):
        JSONMatchesParser.parse(json.dumps(data), 2024)


# Time tests
def test_parse_time_string() -> None:
    data = [make_match({"time_string": "9:15 AM"})]
    parsed = JSONMatchesParser.parse(json.dumps(data), 2024)
    assert parsed[0]["time_string"] == "9:15 AM"


def test_parse_time_utc() -> None:
    data = [make_match({"time_utc": "2024-03-15T14:30:00"})]
    parsed = JSONMatchesParser.parse(json.dumps(data), 2024)
    time = none_throws(parsed[0]["time"])
    assert time is not None
    assert time.year == 2024
    assert time.month == 3
    assert time.day == 15
    assert time.hour == 14
    assert time.minute == 30


def test_parse_time_utc_with_timezone() -> None:
    data = [make_match({"time_utc": "2024-03-15T14:30:00+00:00"})]
    parsed = JSONMatchesParser.parse(json.dumps(data), 2024)
    time = none_throws(parsed[0]["time"])
    assert time is not None
    assert time.tzinfo is None  # Timezone should be stripped


def test_invalid_time_utc_raises_exception() -> None:
    data = [make_match({"time_utc": "invalid date"})]
    with pytest.raises(ParserInputException, match="time_utc"):
        JSONMatchesParser.parse(json.dumps(data), 2024)


def test_parse_actual_start_time_utc() -> None:
    data = [make_match({"actual_start_time_utc": "2024-03-15T14:32:00"})]
    parsed = JSONMatchesParser.parse(json.dumps(data), 2024)
    actual_start_time = none_throws(parsed[0]["actual_start_time"])
    assert actual_start_time is not None
    assert actual_start_time.minute == 32


def test_invalid_actual_start_time_utc_raises_exception() -> None:
    data = [make_match({"actual_start_time_utc": "invalid date"})]
    with pytest.raises(ParserInputException, match="actual_start_time_utc"):
        JSONMatchesParser.parse(json.dumps(data), 2024)


def test_parse_post_results_time_utc() -> None:
    data = [make_match({"post_results_time_utc": "2024-03-15T14:45:00"})]
    parsed = JSONMatchesParser.parse(json.dumps(data), 2024)
    post_results_time = none_throws(parsed[0]["post_results_time"])
    assert post_results_time is not None
    assert post_results_time.minute == 45


def test_invalid_post_results_time_utc_raises_exception() -> None:
    data = [make_match({"post_results_time_utc": "invalid date"})]
    with pytest.raises(ParserInputException, match="post_results_time_utc"):
        JSONMatchesParser.parse(json.dumps(data), 2024)


# Display name tests
def test_parse_display_name() -> None:
    data = [make_match({"display_name": "Match 1"})]
    parsed = JSONMatchesParser.parse(json.dumps(data), 2024)
    assert parsed[0]["display_name"] == "Match 1"


def test_display_name_null_is_valid() -> None:
    data = [make_match({"display_name": None})]
    parsed = JSONMatchesParser.parse(json.dumps(data), 2024)
    assert parsed[0]["display_name"] is None


def test_display_name_non_string_raises_exception() -> None:
    data = [make_match({"display_name": 123})]
    with pytest.raises(ParserInputException, match="display_name"):
        JSONMatchesParser.parse(json.dumps(data), 2024)


# Team key names tests
def test_team_key_names_contains_all_teams() -> None:
    data = [make_match()]
    parsed = JSONMatchesParser.parse(json.dumps(data), 2024)
    team_key_names = parsed[0]["team_key_names"]
    assert "frc254" in team_key_names
    assert "frc971" in team_key_names
    assert "frc1678" in team_key_names
    assert "frc604" in team_key_names
    assert "frc1323" in team_key_names
    assert "frc973" in team_key_names


# Alliances JSON tests
def test_alliances_json_structure() -> None:
    data = [make_match()]
    parsed = JSONMatchesParser.parse(json.dumps(data), 2024)
    alliances = json.loads(parsed[0]["alliances_json"])
    assert AllianceColor.RED in alliances
    assert AllianceColor.BLUE in alliances
    assert "teams" in alliances[AllianceColor.RED]
    assert "score" in alliances[AllianceColor.RED]
    assert "surrogates" in alliances[AllianceColor.RED]
    assert "dqs" in alliances[AllianceColor.RED]


def test_alliances_json_defaults_empty_surrogates_and_dqs() -> None:
    data = [make_match()]
    parsed = JSONMatchesParser.parse(json.dumps(data), 2024)
    alliances = json.loads(parsed[0]["alliances_json"])
    assert alliances[AllianceColor.RED]["surrogates"] == []
    assert alliances[AllianceColor.RED]["dqs"] == []
    assert alliances[AllianceColor.BLUE]["surrogates"] == []
    assert alliances[AllianceColor.BLUE]["dqs"] == []


# Invalid JSON input tests
def test_invalid_json_raises_exception() -> None:
    with pytest.raises(InvalidJson):
        JSONMatchesParser.parse("not valid json", 2024)


def test_non_list_json_raises_exception() -> None:
    with pytest.raises(ParserInputException, match="Invalid JSON"):
        JSONMatchesParser.parse('{"not": "a list"}', 2024)


def test_match_not_dict_raises_exception() -> None:
    with pytest.raises(ParserInputException, match="Matches must be dicts"):
        JSONMatchesParser.parse('["not a dict"]', 2024)
