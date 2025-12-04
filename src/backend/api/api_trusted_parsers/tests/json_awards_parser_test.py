import json

import pytest

from backend.api.api_trusted_parsers.json_awards_parser import JSONAwardsParser
from backend.common.consts.award_type import AwardType
from backend.common.datafeed_parsers.exceptions import ParserInputException


@pytest.fixture
def event_key() -> str:
    return "2020casj"


def test_parse_single_team_award(event_key: str) -> None:
    data = [
        {
            "name_str": "Winner",
            "team_key": "frc254",
        }
    ]
    parsed = JSONAwardsParser.parse(json.dumps(data), event_key)
    assert len(parsed) == 1
    award = parsed[0]
    assert award["name_str"] == "Winner"
    assert award["award_type_enum"] == AwardType.WINNER
    assert award["team_key_list"] == ["frc254"]
    assert len(award["recipient_list"]) == 1
    award_recipient = award["recipient_list"][0]
    assert award_recipient["team_number"] == 254
    assert award_recipient["awardee"] is None


def test_parse_with_explicit_type_enum(event_key: str) -> None:
    data = [
        {
            "name_str": "Tournament Winner",
            "type_enum": AwardType.WINNER,
            "team_key": "frc971",
        }
    ]
    parsed = JSONAwardsParser.parse(json.dumps(data), event_key)
    assert len(parsed) == 1
    award = parsed[0]
    assert award["name_str"] == "Tournament Winner"
    assert award["award_type_enum"] == AwardType.WINNER
    assert award["team_key_list"] == ["frc971"]


def test_parse_individual_award_with_awardee(event_key: str) -> None:
    data = [
        {
            "name_str": "Dean's List",
            "type_enum": AwardType.DEANS_LIST,
            "awardee": "John Doe",
        }
    ]
    parsed = JSONAwardsParser.parse(json.dumps(data), event_key)
    assert len(parsed) == 1
    award = parsed[0]
    assert award["award_type_enum"] == AwardType.DEANS_LIST
    assert award["team_key_list"] == []
    assert len(award["recipient_list"]) == 1
    award_recipient = award["recipient_list"][0]
    assert award_recipient["team_number"] is None
    assert award_recipient["awardee"] == "John Doe"


def test_parse_award_with_team_and_awardee(event_key: str) -> None:
    data = [
        {
            "name_str": "Woodie Flowers Award",
            "type_enum": AwardType.WOODIE_FLOWERS,
            "team_key": "frc254",
            "awardee": "Jane Smith",
        }
    ]
    parsed = JSONAwardsParser.parse(json.dumps(data), event_key)
    assert len(parsed) == 1
    award = parsed[0]
    assert award["team_key_list"] == ["frc254"]
    assert len(award["recipient_list"]) == 1
    award_recipient = award["recipient_list"][0]
    assert award_recipient["team_number"] == 254
    assert award_recipient["awardee"] == "Jane Smith"


def test_parse_multiple_recipients_same_award(event_key: str) -> None:
    data = [
        {
            "name_str": "Winner",
            "team_key": "frc254",
        },
        {
            "name_str": "Winner",
            "team_key": "frc971",
        },
        {
            "name_str": "Winner",
            "team_key": "frc604",
        },
    ]
    parsed = JSONAwardsParser.parse(json.dumps(data), event_key)
    assert len(parsed) == 1
    award = parsed[0]
    assert award["name_str"] == "Winner"
    assert award["team_key_list"] == ["frc254", "frc971", "frc604"]
    assert len(award["recipient_list"]) == 3
    assert award["recipient_list"] == [
        {"team_number": 254, "awardee": None},
        {"team_number": 971, "awardee": None},
        {"team_number": 604, "awardee": None},
    ]


def test_parse_multiple_different_awards(event_key: str) -> None:
    data = [
        {
            "name_str": "Winner",
            "team_key": "frc254",
        },
        {
            "name_str": "Finalist",
            "team_key": "frc1678",
        },
    ]
    parsed = JSONAwardsParser.parse(json.dumps(data), event_key)
    assert len(parsed) == 2
    award_types = {award["award_type_enum"] for award in parsed}
    assert AwardType.WINNER in award_types
    assert AwardType.FINALIST in award_types


def test_parse_bytes_input(event_key: str) -> None:
    data = [
        {
            "name_str": "Winner",
            "team_key": "frc254",
        }
    ]
    parsed = JSONAwardsParser.parse(json.dumps(data).encode("utf-8"), event_key)
    assert len(parsed) == 1
    assert parsed[0]["award_type_enum"] == AwardType.WINNER


def test_missing_name_str_raises_exception(event_key: str) -> None:
    data = [
        {
            "name_str": "",
            "team_key": "frc254",
        }
    ]
    with pytest.raises(ParserInputException, match="name_str"):
        JSONAwardsParser.parse(json.dumps(data), event_key)


def test_bad_team_key_format_raises_exception(event_key: str) -> None:
    data = [
        {
            "name_str": "Winner",
            "team_key": "254",
        }
    ]
    with pytest.raises(ParserInputException, match="Bad team_key"):
        JSONAwardsParser.parse(json.dumps(data), event_key)


def test_bad_team_key_format_with_letters_raises_exception(event_key: str) -> None:
    data = [
        {
            "name_str": "Winner",
            "team_key": "frcABC",
        }
    ]
    with pytest.raises(ParserInputException, match="Bad team_key"):
        JSONAwardsParser.parse(json.dumps(data), event_key)


def test_unknown_award_type_without_name_match_raises_exception(event_key: str) -> None:
    data = [
        {
            "name_str": "Some Unknown Award That Cannot Be Parsed",
            "team_key": "frc254",
        }
    ]
    with pytest.raises(ParserInputException, match="Cannot determine award type"):
        JSONAwardsParser.parse(json.dumps(data), event_key)


def test_no_team_key_or_awardee_raises_exception(event_key: str) -> None:
    data = [
        {
            "name_str": "Winner",
            "type_enum": AwardType.WINNER,
        }
    ]
    with pytest.raises(ParserInputException, match="team_key or awardee"):
        JSONAwardsParser.parse(json.dumps(data), event_key)


def test_null_team_key_with_awardee_is_valid(event_key: str) -> None:
    data = [
        {
            "name_str": "Dean's List",
            "type_enum": AwardType.DEANS_LIST,
            "team_key": None,
            "awardee": "John Doe",
        }
    ]
    parsed = JSONAwardsParser.parse(json.dumps(data), event_key)
    assert len(parsed) == 1
    assert parsed[0]["team_key_list"] == []
    assert parsed[0]["recipient_list"] == [{"team_number": None, "awardee": "John Doe"}]


def test_invalid_type_enum_falls_back_to_name_parsing(event_key: str) -> None:
    data = [
        {
            "name_str": "Winner",
            "type_enum": 9999,  # Invalid type enum
            "team_key": "frc254",
        }
    ]
    parsed = JSONAwardsParser.parse(json.dumps(data), event_key)
    assert len(parsed) == 1
    assert parsed[0]["award_type_enum"] == AwardType.WINNER


def test_parse_chairmans_award(event_key: str) -> None:
    data = [
        {
            "name_str": "Chairman's Award",
            "team_key": "frc254",
        }
    ]
    parsed = JSONAwardsParser.parse(json.dumps(data), event_key)
    assert len(parsed) == 1
    assert parsed[0]["award_type_enum"] == AwardType.CHAIRMANS


def test_parse_engineering_inspiration(event_key: str) -> None:
    data = [
        {
            "name_str": "Engineering Inspiration Award",
            "team_key": "frc1678",
        }
    ]
    parsed = JSONAwardsParser.parse(json.dumps(data), event_key)
    assert len(parsed) == 1
    assert parsed[0]["award_type_enum"] == AwardType.ENGINEERING_INSPIRATION


def test_parse_rookie_all_star(event_key: str) -> None:
    data = [
        {
            "name_str": "Rookie All Star Award",
            "team_key": "frc9999",
        }
    ]
    parsed = JSONAwardsParser.parse(json.dumps(data), event_key)
    assert len(parsed) == 1
    assert parsed[0]["award_type_enum"] == AwardType.ROOKIE_ALL_STAR


def test_parse_empty_list(event_key: str) -> None:
    parsed = JSONAwardsParser.parse("[]", event_key)
    assert parsed == []
