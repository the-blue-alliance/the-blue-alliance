import json

import pytest
from pyre_extensions import none_throws

from backend.api.api_trusted_parsers.json_event_info_parser import JSONEventInfoParser
from backend.common.consts.event_sync_type import EventSyncType
from backend.common.consts.playoff_type import PlayoffType
from backend.common.datafeed_parsers.exceptions import ParserInputException


def test_parse_empty_dict() -> None:
    parsed = JSONEventInfoParser.parse("{}")
    assert parsed == {}


def test_parse_bytes_input() -> None:
    data = {"first_event_code": "CASJ"}
    parsed = JSONEventInfoParser.parse(json.dumps(data).encode("utf-8"))
    assert parsed.get("first_event_code") == "CASJ"


def test_parse_webcast_with_type_and_channel() -> None:
    data = {"webcasts": [{"type": "twitch", "channel": "firstinspires"}]}
    parsed = JSONEventInfoParser.parse(json.dumps(data))
    assert len(none_throws(parsed.get("webcasts"))) == 1
    webcast = none_throws(parsed.get("webcasts"))[0]
    assert webcast["type"] == "twitch"
    assert webcast["channel"] == "firstinspires"


def test_parse_webcast_with_url() -> None:
    data = {"webcasts": [{"url": "https://www.twitch.tv/firstinspires"}]}
    parsed = JSONEventInfoParser.parse(json.dumps(data))
    assert len(none_throws(parsed.get("webcasts"))) == 1
    webcast = none_throws(parsed.get("webcasts"))[0]
    assert webcast["type"] == "twitch"
    assert webcast["channel"] == "firstinspires"


def test_parse_webcast_with_youtube_url() -> None:
    data = {"webcasts": [{"url": "https://www.youtube.com/watch?v=abc123"}]}
    parsed = JSONEventInfoParser.parse(json.dumps(data))
    assert len(none_throws(parsed.get("webcasts"))) == 1
    webcast = none_throws(parsed.get("webcasts"))[0]
    assert webcast["type"] == "youtube"
    assert webcast["channel"] == "abc123"


def test_parse_multiple_webcasts() -> None:
    data = {
        "webcasts": [
            {"type": "twitch", "channel": "firstinspires"},
            {"url": "https://www.youtube.com/watch?v=abc123"},
        ]
    }
    parsed = JSONEventInfoParser.parse(json.dumps(data))
    assert len(none_throws(parsed.get("webcasts"))) == 2
    assert none_throws(parsed.get("webcasts"))[0]["type"] == "twitch"
    assert none_throws(parsed.get("webcasts"))[1]["type"] == "youtube"


def test_parse_webcast_with_date() -> None:
    data = {
        "webcasts": [
            {"type": "twitch", "channel": "firstinspires", "date": "2024-03-15"}
        ]
    }
    parsed = JSONEventInfoParser.parse(json.dumps(data))
    assert len(none_throws(parsed.get("webcasts"))) == 1
    assert none_throws(parsed.get("webcasts"))[0].get("date") == "2024-03-15"


def test_parse_webcast_invalid_date_format_raises_exception() -> None:
    data = {
        "webcasts": [
            {"type": "twitch", "channel": "firstinspires", "date": "03-15-2024"}
        ]
    }
    with pytest.raises(ParserInputException, match="Invalid webcast date"):
        JSONEventInfoParser.parse(json.dumps(data))


def test_parse_webcast_unknown_url_raises_exception() -> None:
    data = {"webcasts": [{"url": "https://example.com/unknown"}]}
    with pytest.raises(ParserInputException, match="Unknown webcast url"):
        JSONEventInfoParser.parse(json.dumps(data))


def test_parse_webcast_invalid_format_raises_exception() -> None:
    data = {"webcasts": [{"type": "twitch"}]}  # Missing channel
    with pytest.raises(ParserInputException, match="Invalid webcast"):
        JSONEventInfoParser.parse(json.dumps(data))


def test_parse_webcast_missing_both_url_and_type_raises_exception() -> None:
    data = {"webcasts": [{"channel": "test"}]}  # Missing type and url
    with pytest.raises(ParserInputException, match="Invalid webcast"):
        JSONEventInfoParser.parse(json.dumps(data))


# Remap teams tests
def test_parse_remap_teams() -> None:
    data = {"remap_teams": {"frc9999": "frc254"}}
    parsed = JSONEventInfoParser.parse(json.dumps(data))
    assert parsed.get("remap_teams") == {"frc9999": "frc254"}


def test_parse_remap_teams_with_suffix() -> None:
    data = {"remap_teams": {"frc9999": "frc254B"}}
    parsed = JSONEventInfoParser.parse(json.dumps(data))
    assert parsed.get("remap_teams") == {"frc9999": "frc254B"}


def test_parse_remap_teams_multiple() -> None:
    data = {"remap_teams": {"frc9998": "frc254", "frc9999": "frc971B"}}
    parsed = JSONEventInfoParser.parse(json.dumps(data))
    assert parsed.get("remap_teams") == {"frc9998": "frc254", "frc9999": "frc971B"}


def test_parse_remap_teams_bad_temp_team_raises_exception() -> None:
    data = {"remap_teams": {"254": "frc254"}}
    with pytest.raises(ParserInputException, match="Bad team"):
        JSONEventInfoParser.parse(json.dumps(data))


def test_parse_remap_teams_bad_temp_team_with_suffix_raises_exception() -> None:
    data = {"remap_teams": {"frc254B": "frc254"}}
    with pytest.raises(ParserInputException, match="Bad team"):
        JSONEventInfoParser.parse(json.dumps(data))


def test_parse_remap_teams_bad_remapped_team_raises_exception() -> None:
    data = {"remap_teams": {"frc9999": "254"}}
    with pytest.raises(ParserInputException, match="Bad team"):
        JSONEventInfoParser.parse(json.dumps(data))


def test_parse_remap_teams_bad_remapped_team_suffix_raises_exception() -> None:
    data = {"remap_teams": {"frc9999": "frc254BB"}}
    with pytest.raises(ParserInputException, match="Bad team"):
        JSONEventInfoParser.parse(json.dumps(data))


def test_parse_remap_teams_bad_temp_team_letters_raises_exception() -> None:
    data = {"remap_teams": {"frcABC": "frc254"}}
    with pytest.raises(ParserInputException, match="Bad team"):
        JSONEventInfoParser.parse(json.dumps(data))


def test_parse_playoff_type_bracket_8_team() -> None:
    data = {"playoff_type": PlayoffType.BRACKET_8_TEAM}
    parsed = JSONEventInfoParser.parse(json.dumps(data))
    assert parsed.get("playoff_type") == PlayoffType.BRACKET_8_TEAM


def test_parse_playoff_type_double_elim() -> None:
    data = {"playoff_type": PlayoffType.DOUBLE_ELIM_8_TEAM}
    parsed = JSONEventInfoParser.parse(json.dumps(data))
    assert parsed.get("playoff_type") == PlayoffType.DOUBLE_ELIM_8_TEAM


def test_parse_playoff_type_round_robin() -> None:
    data = {"playoff_type": PlayoffType.ROUND_ROBIN_6_TEAM}
    parsed = JSONEventInfoParser.parse(json.dumps(data))
    assert parsed.get("playoff_type") == PlayoffType.ROUND_ROBIN_6_TEAM


def test_parse_playoff_type_null() -> None:
    data = {"playoff_type": None}
    parsed = JSONEventInfoParser.parse(json.dumps(data))
    assert parsed.get("playoff_type") is None


def test_parse_playoff_type_invalid_raises_exception() -> None:
    data = {"playoff_type": 9999}
    with pytest.raises(ParserInputException, match="Bad playoff type"):
        JSONEventInfoParser.parse(json.dumps(data))


def test_parse_first_event_code() -> None:
    data = {"first_event_code": "CASJ"}
    parsed = JSONEventInfoParser.parse(json.dumps(data))
    assert parsed.get("first_event_code") == "CASJ"


def test_parse_first_event_code_null() -> None:
    data = {"first_event_code": None}
    parsed = JSONEventInfoParser.parse(json.dumps(data))
    assert parsed.get("first_event_code") is None


def test_parse_timezone() -> None:
    data = {"timezone": "America/Los_Angeles"}
    parsed = JSONEventInfoParser.parse(json.dumps(data))
    assert parsed.get("timezone") == "America/Los_Angeles"


def test_parse_timezone_invalid_raises_exception() -> None:
    data = {"timezone": "Invalid/Timezone"}
    with pytest.raises(ParserInputException, match="Unknown timezone"):
        JSONEventInfoParser.parse(json.dumps(data))


def test_parse_disable_sync_alliances() -> None:
    data = {"disable_sync": {"event_alliances": True}}
    parsed = JSONEventInfoParser.parse(json.dumps(data))
    assert parsed.get("sync_disabled_flags") == EventSyncType.EVENT_ALLIANCES


def test_parse_disable_sync_rankings() -> None:
    data = {"disable_sync": {"event_rankings": True}}
    parsed = JSONEventInfoParser.parse(json.dumps(data))
    assert parsed.get("sync_disabled_flags") == EventSyncType.EVENT_RANKINGS


def test_parse_disable_sync_multiple_flags() -> None:
    data = {
        "disable_sync": {
            "event_alliances": True,
            "event_rankings": True,
            "event_qual_matches": True,
        }
    }
    parsed = JSONEventInfoParser.parse(json.dumps(data))
    expected_flags = (
        EventSyncType.EVENT_ALLIANCES
        | EventSyncType.EVENT_RANKINGS
        | EventSyncType.EVENT_QUAL_MATCHES
    )
    assert parsed.get("sync_disabled_flags") == expected_flags


def test_parse_disable_sync_all_flags() -> None:
    data = {
        "disable_sync": {
            "event_alliances": True,
            "event_rankings": True,
            "event_qual_matches": True,
            "event_playoff_matches": True,
            "event_awards": True,
        }
    }
    parsed = JSONEventInfoParser.parse(json.dumps(data))
    expected_flags = (
        EventSyncType.EVENT_ALLIANCES
        | EventSyncType.EVENT_RANKINGS
        | EventSyncType.EVENT_QUAL_MATCHES
        | EventSyncType.EVENT_PLAYOFF_MATCHES
        | EventSyncType.EVENT_AWARDS
    )
    assert parsed.get("sync_disabled_flags") == expected_flags


def test_parse_disable_sync_false_values_ignored() -> None:
    data = {"disable_sync": {"event_alliances": True, "event_rankings": False}}
    parsed = JSONEventInfoParser.parse(json.dumps(data))
    assert parsed.get("sync_disabled_flags") == EventSyncType.EVENT_ALLIANCES


def test_parse_disable_sync_all_false_is_zero() -> None:
    data = {"disable_sync": {"event_alliances": False}}
    parsed = JSONEventInfoParser.parse(json.dumps(data))
    assert parsed.get("sync_disabled_flags") == 0


def test_parse_disable_sync_invalid_key_raises_exception() -> None:
    data = {"disable_sync": {"invalid_key": True}}
    with pytest.raises(ParserInputException, match="Invalid keys in disable_sync"):
        JSONEventInfoParser.parse(json.dumps(data))


def test_parse_disable_sync_multiple_invalid_keys_raises_exception() -> None:
    data = {"disable_sync": {"invalid_key1": True, "invalid_key2": True}}
    with pytest.raises(ParserInputException, match="Invalid keys in disable_sync"):
        JSONEventInfoParser.parse(json.dumps(data))


def test_parse_disable_sync_non_dict_raises_exception() -> None:
    data = {"disable_sync": "not_a_dict"}
    with pytest.raises((ParserInputException)):
        JSONEventInfoParser.parse(json.dumps(data))


def test_parse_multiple_fields() -> None:
    data = {
        "first_event_code": "CASJ",
        "playoff_type": PlayoffType.BRACKET_8_TEAM,
        "webcasts": [{"type": "twitch", "channel": "firstinspires"}],
        "remap_teams": {"frc9999": "frc254"},
        "timezone": "America/Los_Angeles",
        "disable_sync": {"event_alliances": True},
    }
    parsed = JSONEventInfoParser.parse(json.dumps(data))
    assert parsed.get("first_event_code") == "CASJ"
    assert parsed.get("playoff_type") == PlayoffType.BRACKET_8_TEAM
    assert len(none_throws(parsed.get("webcasts"))) == 1
    assert parsed.get("remap_teams") == {"frc9999": "frc254"}
    assert parsed.get("timezone") == "America/Los_Angeles"
    assert parsed.get("sync_disabled_flags") == EventSyncType.EVENT_ALLIANCES
