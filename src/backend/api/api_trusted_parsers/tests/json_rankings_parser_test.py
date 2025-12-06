import json

import pytest
from pyre_extensions.safe_json import InvalidJson

from backend.api.api_trusted_parsers.json_rankings_parser import JSONRankingsParser
from backend.common.datafeed_parsers.exceptions import ParserInputException


def test_parse_single_ranking() -> None:
    data = {
        "breakdowns": ["QS", "Auton", "Teleop"],
        "rankings": [
            {
                "rank": 1,
                "team_key": "frc254",
                "played": 10,
                "dqs": 0,
                "wins": 8,
                "losses": 2,
                "ties": 0,
                "QS": 24.0,
                "Auton": 150.0,
                "Teleop": 200.0,
            }
        ],
    }
    parsed = JSONRankingsParser.parse(2024, json.dumps(data))
    assert len(parsed) == 1
    ranking = parsed[0]
    assert ranking["rank"] == 1
    assert ranking["team_key"] == "frc254"
    assert ranking["matches_played"] == 10
    assert ranking["dq"] == 0
    assert ranking["record"] == {"wins": 8, "losses": 2, "ties": 0}
    assert ranking["sort_orders"] == [24.0, 150.0, 200.0]


def test_parse_multiple_rankings() -> None:
    data = {
        "breakdowns": ["QS"],
        "rankings": [
            {
                "rank": 1,
                "team_key": "frc254",
                "played": 10,
                "dqs": 0,
                "QS": 24.0,
            },
            {
                "rank": 2,
                "team_key": "frc971",
                "played": 10,
                "dqs": 1,
                "QS": 22.0,
            },
            {
                "rank": 3,
                "team_key": "frc1678",
                "played": 10,
                "dqs": 0,
                "QS": 20.0,
            },
        ],
    }
    parsed = JSONRankingsParser.parse(2024, json.dumps(data))
    assert len(parsed) == 3
    assert parsed[0]["rank"] == 1
    assert parsed[0]["team_key"] == "frc254"
    assert parsed[1]["rank"] == 2
    assert parsed[1]["team_key"] == "frc971"
    assert parsed[2]["rank"] == 3
    assert parsed[2]["team_key"] == "frc1678"


def test_parse_bytes_input() -> None:
    data = {
        "breakdowns": [],
        "rankings": [
            {
                "rank": 1,
                "team_key": "frc254",
                "played": 5,
                "dqs": 0,
            }
        ],
    }
    parsed = JSONRankingsParser.parse(2024, json.dumps(data).encode("utf-8"))
    assert len(parsed) == 1
    assert parsed[0]["team_key"] == "frc254"


def test_parse_empty_rankings() -> None:
    data = {
        "breakdowns": [],
        "rankings": [],
    }
    parsed = JSONRankingsParser.parse(2024, json.dumps(data))
    assert len(parsed) == 0


def test_parse_with_qual_average_in_2015() -> None:
    data = {
        "breakdowns": [],
        "rankings": [
            {
                "rank": 1,
                "team_key": "frc254",
                "played": 10,
                "dqs": 0,
                "qual_average": 75.5,
            }
        ],
    }
    parsed = JSONRankingsParser.parse(2015, json.dumps(data))
    assert len(parsed) == 1
    assert parsed[0]["qual_average"] == 75.5
    # 2015 is a NO_RECORD_YEAR
    assert parsed[0]["record"] is None


def test_parse_qual_average_ignored_in_non_2015_year() -> None:
    data = {
        "breakdowns": [],
        "rankings": [
            {
                "rank": 1,
                "team_key": "frc254",
                "played": 10,
                "dqs": 0,
                "qual_average": 75.5,
            }
        ],
    }
    parsed = JSONRankingsParser.parse(2024, json.dumps(data))
    assert len(parsed) == 1
    assert parsed[0]["qual_average"] is None


def test_parse_no_record_in_2010() -> None:
    data = {
        "breakdowns": [],
        "rankings": [
            {
                "rank": 1,
                "team_key": "frc254",
                "played": 10,
                "dqs": 0,
                "wins": 8,
                "losses": 2,
                "ties": 0,
            }
        ],
    }
    parsed = JSONRankingsParser.parse(2010, json.dumps(data))
    assert len(parsed) == 1
    assert parsed[0]["record"] is None


def test_parse_no_record_in_2021() -> None:
    data = {
        "breakdowns": [],
        "rankings": [
            {
                "rank": 1,
                "team_key": "frc254",
                "played": 10,
                "dqs": 0,
                "wins": 8,
                "losses": 2,
                "ties": 0,
            }
        ],
    }
    parsed = JSONRankingsParser.parse(2021, json.dumps(data))
    assert len(parsed) == 1
    assert parsed[0]["record"] is None


def test_parse_wins_losses_ties_in_breakdowns_removed() -> None:
    data = {
        "breakdowns": ["wins", "losses", "ties", "QS"],
        "rankings": [
            {
                "rank": 1,
                "team_key": "frc254",
                "played": 10,
                "dqs": 0,
                "wins": 8,
                "losses": 2,
                "ties": 0,
                "QS": 24.0,
            }
        ],
    }
    parsed = JSONRankingsParser.parse(2024, json.dumps(data))
    assert len(parsed) == 1
    # wins, losses, ties should be removed from sort_orders
    assert parsed[0]["sort_orders"] == [24.0]


def test_parse_default_wins_losses_ties_to_zero() -> None:
    data = {
        "breakdowns": [],
        "rankings": [
            {
                "rank": 1,
                "team_key": "frc254",
                "played": 10,
                "dqs": 0,
            }
        ],
    }
    parsed = JSONRankingsParser.parse(2024, json.dumps(data))
    assert len(parsed) == 1
    assert parsed[0]["record"] == {"wins": 0, "losses": 0, "ties": 0}


def test_parse_invalid_json_raises_exception() -> None:
    with pytest.raises(InvalidJson):
        JSONRankingsParser.parse(2024, "not valid json")


def test_parse_non_dict_raises_exception() -> None:
    with pytest.raises(ParserInputException, match="Data must be a dict"):
        JSONRankingsParser.parse(2024, "[]")


def test_parse_missing_breakdowns_raises_exception() -> None:
    data = {
        "rankings": [
            {
                "rank": 1,
                "team_key": "frc254",
                "played": 10,
                "dqs": 0,
            }
        ],
    }
    with pytest.raises(ParserInputException, match="breakdowns"):
        JSONRankingsParser.parse(2024, json.dumps(data))


def test_parse_breakdowns_not_list_raises_exception() -> None:
    data = {
        "breakdowns": "not_a_list",
        "rankings": [],
    }
    with pytest.raises(ParserInputException, match="breakdowns"):
        JSONRankingsParser.parse(2024, json.dumps(data))


def test_parse_missing_rankings_raises_exception() -> None:
    data = {
        "breakdowns": [],
    }
    with pytest.raises(ParserInputException, match="rankings"):
        JSONRankingsParser.parse(2024, json.dumps(data))


def test_parse_rankings_not_list_raises_exception() -> None:
    data = {
        "breakdowns": [],
        "rankings": "not_a_list",
    }
    with pytest.raises(ParserInputException, match="rankings"):
        JSONRankingsParser.parse(2024, json.dumps(data))


def test_parse_ranking_not_dict_raises_exception() -> None:
    data = {
        "breakdowns": [],
        "rankings": ["not_a_dict"],
    }
    with pytest.raises(ParserInputException, match="Ranking must be a dict"):
        JSONRankingsParser.parse(2024, json.dumps(data))


def test_parse_missing_team_key_raises_exception() -> None:
    data = {
        "breakdowns": [],
        "rankings": [
            {
                "rank": 1,
                "played": 10,
                "dqs": 0,
            }
        ],
    }
    with pytest.raises(ParserInputException, match="team_key"):
        JSONRankingsParser.parse(2024, json.dumps(data))


def test_parse_invalid_team_key_format_raises_exception() -> None:
    data = {
        "breakdowns": [],
        "rankings": [
            {
                "rank": 1,
                "team_key": "254",
                "played": 10,
                "dqs": 0,
            }
        ],
    }
    with pytest.raises(ParserInputException, match="team_key"):
        JSONRankingsParser.parse(2024, json.dumps(data))


def test_parse_invalid_team_key_with_letters_raises_exception() -> None:
    data = {
        "breakdowns": [],
        "rankings": [
            {
                "rank": 1,
                "team_key": "frcABC",
                "played": 10,
                "dqs": 0,
            }
        ],
    }
    with pytest.raises(ParserInputException, match="team_key"):
        JSONRankingsParser.parse(2024, json.dumps(data))


def test_parse_missing_rank_raises_exception() -> None:
    data = {
        "breakdowns": [],
        "rankings": [
            {
                "team_key": "frc254",
                "played": 10,
                "dqs": 0,
            }
        ],
    }
    with pytest.raises(ParserInputException, match="rank"):
        JSONRankingsParser.parse(2024, json.dumps(data))


def test_parse_rank_not_integer_raises_exception() -> None:
    data = {
        "breakdowns": [],
        "rankings": [
            {
                "rank": "1",
                "team_key": "frc254",
                "played": 10,
                "dqs": 0,
            }
        ],
    }
    with pytest.raises(ParserInputException, match="rank"):
        JSONRankingsParser.parse(2024, json.dumps(data))


def test_parse_missing_played_raises_exception() -> None:
    data = {
        "breakdowns": [],
        "rankings": [
            {
                "rank": 1,
                "team_key": "frc254",
                "dqs": 0,
            }
        ],
    }
    with pytest.raises(ParserInputException, match="played"):
        JSONRankingsParser.parse(2024, json.dumps(data))


def test_parse_played_not_integer_raises_exception() -> None:
    data = {
        "breakdowns": [],
        "rankings": [
            {
                "rank": 1,
                "team_key": "frc254",
                "played": "10",
                "dqs": 0,
            }
        ],
    }
    with pytest.raises(ParserInputException, match="played"):
        JSONRankingsParser.parse(2024, json.dumps(data))


def test_parse_missing_dqs_raises_exception() -> None:
    data = {
        "breakdowns": [],
        "rankings": [
            {
                "rank": 1,
                "team_key": "frc254",
                "played": 10,
            }
        ],
    }
    with pytest.raises(ParserInputException, match="dqs"):
        JSONRankingsParser.parse(2024, json.dumps(data))


def test_parse_dqs_not_integer_raises_exception() -> None:
    data = {
        "breakdowns": [],
        "rankings": [
            {
                "rank": 1,
                "team_key": "frc254",
                "played": 10,
                "dqs": "0",
            }
        ],
    }
    with pytest.raises(ParserInputException, match="dqs"):
        JSONRankingsParser.parse(2024, json.dumps(data))


def test_parse_with_multiple_breakdowns() -> None:
    data = {
        "breakdowns": ["Ranking Points", "Match Points", "Auton", "Teleop", "Endgame"],
        "rankings": [
            {
                "rank": 1,
                "team_key": "frc254",
                "played": 10,
                "dqs": 0,
                "Ranking Points": 24.0,
                "Match Points": 300.0,
                "Auton": 100.0,
                "Teleop": 150.0,
                "Endgame": 50.0,
            }
        ],
    }
    parsed = JSONRankingsParser.parse(2024, json.dumps(data))
    assert len(parsed) == 1
    assert parsed[0]["sort_orders"] == [24.0, 300.0, 100.0, 150.0, 50.0]


def test_parse_breakdown_values_converted_to_float() -> None:
    data = {
        "breakdowns": ["QS"],
        "rankings": [
            {
                "rank": 1,
                "team_key": "frc254",
                "played": 10,
                "dqs": 0,
                "QS": 24,  # Integer, should be converted to float
            }
        ],
    }
    parsed = JSONRankingsParser.parse(2024, json.dumps(data))
    assert len(parsed) == 1
    assert parsed[0]["sort_orders"] == [24.0]
    assert isinstance(parsed[0]["sort_orders"][0], float)


def test_parse_invalid_breakdown_value_defaults_to_zero() -> None:
    data = {
        "breakdowns": ["QS"],
        "rankings": [
            {
                "rank": 1,
                "team_key": "frc254",
                "played": 10,
                "dqs": 0,
                "QS": "not_a_number",
            }
        ],
    }
    parsed = JSONRankingsParser.parse(2024, json.dumps(data))
    assert len(parsed) == 1
    assert parsed[0]["sort_orders"] == [0.0]


def test_parse_with_breakdowns_dict() -> None:
    data = {
        "breakdowns": ["QS", "Auton"],
        "rankings": [
            {
                "rank": 1,
                "team_key": "frc254",
                "played": 10,
                "dqs": 0,
                "breakdowns": {"QS": 24.0, "Auton": 150.0},
                "QS": 24.0,
                "Auton": 150.0,
            }
        ],
    }
    parsed = JSONRankingsParser.parse(2024, json.dumps(data))
    assert len(parsed) == 1
    assert parsed[0]["sort_orders"] == [24.0, 150.0]
