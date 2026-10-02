import json
from datetime import datetime
from typing import Any, cast, Dict, List, Optional, Tuple

import pytest

from backend.common.consts.alliance_color import AllianceColor
from backend.common.consts.comp_level import CompLevel
from backend.common.consts.event_type import EventType
from backend.common.consts.playoff_type import PlayoffType
from backend.common.frc_api.types import EventScheduleHybridModelV2
from backend.common.helpers.match_helper import MatchHelper
from backend.common.models.alliance import MatchAlliance
from backend.common.models.event import Event
from backend.common.models.match import Match
from backend.tasks_io.datafeeds.parsers.fms_api.fms_api_match_parser import (
    FMSAPIHybridScheduleParser,
)


def test_parse_no_matches(ndb_stub, test_data_importer) -> None:
    event = Event(
        id="2016nyny",
        name="NYC Regional",
        event_type_enum=EventType.REGIONAL,
        short_name="NYC",
        event_short="nyny",
        year=2016,
        end_date=datetime(2016, 3, 27),
        official=True,
        start_date=datetime(2016, 3, 24),
        timezone_id="America/New_York",
    )
    event.put()
    path = test_data_importer._get_path(
        __file__, "data/2016_hybrid_schedule_no_matches.json"
    )
    with open(path, "r") as f:
        matches, _ = FMSAPIHybridScheduleParser(2016, "nyny").parse(
            json.loads(f.read())
        )

        assert isinstance(matches, list)
        assert len(matches) == 0


def test_parse_qual(ndb_stub, test_data_importer) -> None:
    event = Event(
        id="2016nyny",
        name="NYC Regional",
        event_type_enum=EventType.REGIONAL,
        short_name="NYC",
        event_short="nyny",
        year=2016,
        end_date=datetime(2016, 3, 27),
        official=True,
        start_date=datetime(2016, 3, 24),
        timezone_id="America/New_York",
    )
    event.put()
    path = test_data_importer._get_path(
        __file__, "data/2016_nyny_hybrid_schedule_qual.json"
    )
    with open(path, "r") as f:
        matches, _ = FMSAPIHybridScheduleParser(2016, "nyny").parse(
            json.loads(f.read())
        )

        assert isinstance(matches, list)
        assert len(matches) == 88

        # Assert we get enough of each match type
        count, clean_matches = MatchHelper.organized_matches(matches)
        assert count == 88
        assert len(clean_matches[CompLevel.QM]) == 88

    # Changed format in 2018
    path = test_data_importer._get_path(
        __file__, "data/2016_nyny_hybrid_schedule_qual_2018update.json"
    )
    with open(path, "r") as f:
        matches, _ = FMSAPIHybridScheduleParser(2016, "nyny").parse(
            json.loads(f.read())
        )

        assert isinstance(matches, list)
        assert len(matches) == 88

        # Assert we get enough of each match type
        count, clean_matches = MatchHelper.organized_matches(matches)
        assert count == 88
        assert len(clean_matches[CompLevel.QM]) == 88


def test_parse_playoff(ndb_stub, test_data_importer) -> None:
    event = Event(
        id="2016nyny",
        name="NYC Regional",
        event_type_enum=EventType.REGIONAL,
        short_name="NYC",
        event_short="nyny",
        year=2016,
        end_date=datetime(2016, 3, 27),
        official=True,
        start_date=datetime(2016, 3, 24),
        timezone_id="America/New_York",
    )
    event.put()
    path = test_data_importer._get_path(
        __file__, "data/2016_nyny_hybrid_schedule_playoff.json"
    )
    with open(path, "r") as f:
        matches, _ = FMSAPIHybridScheduleParser(2016, "nyny").parse(
            json.loads(f.read())
        )

        assert isinstance(matches, list)
        assert len(matches) == 15

        # Assert we get enough of each match type
        _, clean_matches = MatchHelper.organized_matches(matches)
        assert len(clean_matches[CompLevel.EF]) == 0
        assert len(clean_matches[CompLevel.QF]) == 9
        assert len(clean_matches[CompLevel.SF]) == 4
        assert len(clean_matches[CompLevel.F]) == 2


def test_parse_playoff_with_octofinals(ndb_stub, test_data_importer) -> None:
    event = Event(
        id="2016micmp",
        name="Michigan District Champs",
        event_type_enum=EventType.DISTRICT_CMP,
        short_name="Michigan",
        event_short="micmp",
        year=2016,
        end_date=datetime(2016, 3, 27),
        official=True,
        start_date=datetime(2016, 3, 24),
        timezone_id="America/New_York",
        playoff_type=PlayoffType.BRACKET_16_TEAM,
    )
    event.put()

    path = test_data_importer._get_path(
        __file__, "data/2016_micmp_staging_hybrid_schedule_playoff.json"
    )
    with open(path, "r") as f:
        matches, _ = FMSAPIHybridScheduleParser(2016, "micmp").parse(
            json.loads(f.read())
        )

        assert isinstance(matches, list)

        assert len(matches) == 36

        # Assert we get enough of each match type
        _, clean_matches = MatchHelper.organized_matches(matches)
        assert len(clean_matches[CompLevel.EF]) == 20
        assert len(clean_matches[CompLevel.QF]) == 10
        assert len(clean_matches[CompLevel.SF]) == 4
        assert len(clean_matches[CompLevel.F]) == 2


def test_parse_2015_playoff(ndb_stub, test_data_importer) -> None:
    event = Event(
        id="2015nyny",
        name="NYC Regional",
        event_type_enum=EventType.REGIONAL,
        short_name="NYC",
        event_short="nyny",
        year=2015,
        end_date=datetime(2015, 3, 27),
        official=True,
        start_date=datetime(2015, 3, 24),
        timezone_id="America/New_York",
        playoff_type=PlayoffType.AVG_SCORE_8_TEAM,
    )
    event.put()
    path = test_data_importer._get_path(
        __file__, "data/2015nyny_hybrid_schedule_playoff.json"
    )
    with open(path, "r") as f:
        matches, _ = FMSAPIHybridScheduleParser(2015, "nyny").parse(
            json.loads(f.read())
        )

        assert isinstance(matches, list)
        assert len(matches) == 17

        # Assert we get enough of each match type
        _, clean_matches = MatchHelper.organized_matches(matches)
        assert len(clean_matches[CompLevel.EF]) == 0
        assert len(clean_matches[CompLevel.QF]) == 8
        assert len(clean_matches[CompLevel.SF]) == 6
        assert len(clean_matches[CompLevel.F]) == 3


def test_parse_2015_playoff_repairs_null_team(ndb_stub, test_data_importer) -> None:
    """A null team in a 2015 playoff match is refilled from playoff advancement."""
    Event(
        id="2015nyny",
        name="NYC Regional",
        event_type_enum=EventType.REGIONAL,
        short_name="NYC",
        event_short="nyny",
        year=2015,
        end_date=datetime(2015, 3, 27),
        official=True,
        start_date=datetime(2015, 3, 24),
        timezone_id="America/New_York",
        playoff_type=PlayoffType.AVG_SCORE_8_TEAM,
    ).put()
    path = test_data_importer._get_path(
        __file__, "data/2015nyny_hybrid_schedule_playoff.json"
    )
    with open(path, "r") as f:
        data = json.loads(f.read())

    # 2015nyny_sf1m1 is 354/694/271 vs 1660/743/4856, the QF #2 and #4 seeds.
    sf1m1 = next(m for m in data["Schedule"] if m["matchNumber"] == 9)
    assert sf1m1["description"] == "Semifinal 1"
    red1 = next(t for t in sf1m1["Teams"] if t["station"] == "Red1")
    assert red1["teamNumber"] == 354
    red1["teamNumber"] = None

    matches, _ = FMSAPIHybridScheduleParser(2015, "nyny").parse(data)

    by_key = {m.key_name: m for m in matches}
    assert len(matches) == 17
    repaired = by_key["2015nyny_sf1m1"]
    assert repaired.alliances[AllianceColor.RED]["teams"] == [
        "frc354",
        "frc694",
        "frc271",
    ]
    assert repaired.alliances[AllianceColor.BLUE]["teams"] == [
        "frc1660",
        "frc743",
        "frc4856",
    ]
    assert sorted(repaired.team_key_names) == sorted(
        ["frc354", "frc694", "frc271", "frc1660", "frc743", "frc4856"]
    )
    for match in matches:
        assert "frcNone" not in match.team_key_names
        for color in [AllianceColor.RED, AllianceColor.BLUE]:
            assert len(match.alliances[color]["teams"]) == 3, match.key_name


def test_parse_2015_playoff_repairs_null_team_in_finals(
    ndb_stub, test_data_importer
) -> None:
    """A null team in a 2015 final is refilled from semifinal advancement."""
    Event(
        id="2015nyny",
        name="NYC Regional",
        event_type_enum=EventType.REGIONAL,
        short_name="NYC",
        event_short="nyny",
        year=2015,
        end_date=datetime(2015, 3, 27),
        official=True,
        start_date=datetime(2015, 3, 24),
        timezone_id="America/New_York",
        playoff_type=PlayoffType.AVG_SCORE_8_TEAM,
    ).put()
    path = test_data_importer._get_path(
        __file__, "data/2015nyny_hybrid_schedule_playoff.json"
    )
    with open(path, "r") as f:
        data = json.loads(f.read())

    # 2015nyny_f1m1 is 2344/1884/1796 vs 354/694/271, the SF #1 and #2 seeds.
    f1m1 = next(m for m in data["Schedule"] if m["matchNumber"] == 15)
    blue3 = next(t for t in f1m1["Teams"] if t["station"] == "Blue3")
    assert blue3["teamNumber"] == 271
    blue3["teamNumber"] = None

    matches, _ = FMSAPIHybridScheduleParser(2015, "nyny").parse(data)

    by_key = {m.key_name: m for m in matches}
    assert len(matches) == 17
    repaired = by_key["2015nyny_f1m1"]
    assert repaired.alliances[AllianceColor.RED]["teams"] == [
        "frc2344",
        "frc1884",
        "frc1796",
    ]
    assert repaired.alliances[AllianceColor.BLUE]["teams"] == [
        "frc354",
        "frc694",
        "frc271",
    ]


def test_parse_2017micmp(ndb_stub, test_data_importer) -> None:
    # 2017micmp is a 4 team bracket that starts playoff match numbering at 1
    event = Event(
        id="2017micmp",
        name="Michigan District Champs",
        event_type_enum=EventType.DISTRICT_CMP,
        short_name="Michigan",
        event_short="micmp",
        year=2017,
        end_date=datetime(2017, 3, 27),
        official=True,
        start_date=datetime(2017, 3, 24),
        timezone_id="America/New_York",
        playoff_type=PlayoffType.BRACKET_4_TEAM,
    )
    event.put()

    path = test_data_importer._get_path(
        __file__, "data/2017micmp_playoff_schedule.json"
    )
    with open(path, "r") as f:
        matches, _ = FMSAPIHybridScheduleParser(2017, "micmp").parse(
            json.loads(f.read())
        )

        assert isinstance(matches, list)

        assert len(matches) == 6

        # Assert we get enough of each match type
        _, clean_matches = MatchHelper.organized_matches(matches)
        assert len(clean_matches[CompLevel.EF]) == 0
        assert len(clean_matches[CompLevel.QF]) == 0
        assert len(clean_matches[CompLevel.SF]) == 4
        assert len(clean_matches[CompLevel.F]) == 2


def test_parse_2champs_einstein(ndb_stub, test_data_importer) -> None:
    event = Event(
        id="2017cmptx",
        name="Einstein (Houston)",
        event_type_enum=EventType.CMP_FINALS,
        short_name="Einstein",
        event_short="cmptx",
        year=2017,
        end_date=datetime(2017, 3, 27),
        official=True,
        start_date=datetime(2017, 3, 24),
        timezone_id="America/New_York",
        playoff_type=PlayoffType.ROUND_ROBIN_6_TEAM,
    )
    event.put()

    path = test_data_importer._get_path(
        __file__, "data/2017cmptx_staging_playoff_schedule.json"
    )
    with open(path, "r") as f:
        matches, _ = FMSAPIHybridScheduleParser(2017, "cmptx").parse(
            json.loads(f.read())
        )

        assert isinstance(matches, list)

        assert len(matches) == 18

        # Assert we get enough of each match type
        _, clean_matches = MatchHelper.organized_matches(matches)
        assert len(clean_matches[CompLevel.EF]) == 0
        assert len(clean_matches[CompLevel.QF]) == 0
        assert len(clean_matches[CompLevel.SF]) == 15
        assert len(clean_matches[CompLevel.F]) == 3


def test_parse_foc_b05(ndb_stub, test_data_importer) -> None:
    event = Event(
        id="2017nhfoc",
        name="FIRST Festival of Champions",
        event_type_enum=EventType.CMP_FINALS,
        short_name="FIRST Festival of Champions",
        event_short="nhfoc",
        first_code="foc",
        year=2017,
        end_date=datetime(2017, 7, 29),
        official=True,
        start_date=datetime(2017, 7, 29),
        timezone_id="America/New_York",
        playoff_type=PlayoffType.BO5_FINALS,
    )
    event.put()

    path = test_data_importer._get_path(
        __file__, "data/2017foc_staging_hybrid_schedule_playoff.json"
    )
    with open(path, "r") as f:
        matches, _ = FMSAPIHybridScheduleParser(2017, "nhfoc").parse(
            json.loads(f.read())
        )

        assert isinstance(matches, list)

        assert len(matches) == 5

        # Assert we get enough of each match type
        _, clean_matches = MatchHelper.organized_matches(matches)
        assert len(clean_matches[CompLevel.EF]) == 0
        assert len(clean_matches[CompLevel.QF]) == 0
        assert len(clean_matches[CompLevel.SF]) == 0
        assert len(clean_matches[CompLevel.F]) == 5

        for i, match in enumerate(clean_matches[CompLevel.F]):
            assert match.set_number == 1
            assert match.match_number == i + 1


def _make_sf_match(alliances_json: str, score_breakdown_json: str) -> Match:
    return Match(
        id="2026mefal_sf1m1",
        year=2026,
        comp_level=CompLevel.SF,
        set_number=1,
        match_number=1,
        alliances_json=alliances_json,
        score_breakdown_json=score_breakdown_json,
    )


def test_is_blank_match_qual_always_false() -> None:
    """Qual matches are never considered blank."""
    match = Match(
        id="2026mefal_qm1",
        year=2026,
        comp_level=CompLevel.QM,
        set_number=1,
        match_number=1,
    )
    assert FMSAPIHybridScheduleParser.is_blank_match(match) is False


def test_is_blank_match_no_score_breakdown() -> None:
    """Playoff matches with no score breakdown are not blank."""
    match = Match(
        id="2026mefal_sf1m1",
        year=2026,
        comp_level=CompLevel.SF,
        set_number=1,
        match_number=1,
    )
    assert FMSAPIHybridScheduleParser.is_blank_match(match) is False


def test_is_blank_match_nonzero_score() -> None:
    """Playoff match where an alliance has nonzero score is not blank."""
    alliances = {
        "red": MatchAlliance(teams=["frc1", "frc2", "frc3"], score=534),
        "blue": MatchAlliance(teams=["frc4", "frc5", "frc6"], score=0),
    }
    breakdown = {
        "red": {"totalPoints": 534},
        "blue": {"totalPoints": 0},
    }
    match = _make_sf_match(json.dumps(alliances), json.dumps(breakdown))
    assert FMSAPIHybridScheduleParser.is_blank_match(match) is False


def test_is_blank_match_all_zero_flat_breakdown() -> None:
    """Playoff match where both alliances have score=0 and all-zero breakdown is blank."""
    alliances = {
        "red": MatchAlliance(teams=["frc1", "frc2", "frc3"], score=0),
        "blue": MatchAlliance(teams=["frc4", "frc5", "frc6"], score=0),
    }
    breakdown = {
        "red": {"totalPoints": 0, "autoPoints": 0, "teleopPoints": 0},
        "blue": {"totalPoints": 0, "autoPoints": 0, "teleopPoints": 0},
    }
    match = _make_sf_match(json.dumps(alliances), json.dumps(breakdown))
    assert FMSAPIHybridScheduleParser.is_blank_match(match) is True


def test_is_blank_match_all_zero_with_nested_dict() -> None:
    """2026-style breakdown with hubScore nested dict of all zeros is still blank."""
    hub_score_zero = {
        "autoCount": 0,
        "transitionCount": 0,
        "shift1Count": 0,
        "shift2Count": 0,
        "shift3Count": 0,
        "shift4Count": 0,
        "endgameCount": 0,
        "teleopCount": 0,
        "totalCount": 0,
        "uncounted": 0,
        "autoPoints": 0,
        "transitionPoints": 0,
        "shift1Points": 0,
        "shift2Points": 0,
        "shift3Points": 0,
        "shift4Points": 0,
        "endgamePoints": 0,
        "teleopPoints": 0,
        "totalPoints": 0,
    }
    alliances = {
        "red": MatchAlliance(teams=["frc1", "frc2", "frc3"], score=0),
        "blue": MatchAlliance(teams=["frc4", "frc5", "frc6"], score=0),
    }
    breakdown = {
        "red": {"totalPoints": 0, "hubScore": hub_score_zero, "penalties": "None"},
        "blue": {"totalPoints": 0, "hubScore": hub_score_zero, "penalties": "None"},
    }
    match = _make_sf_match(json.dumps(alliances), json.dumps(breakdown))
    assert FMSAPIHybridScheduleParser.is_blank_match(match) is True


def test_is_blank_match_nonzero_nested_dict() -> None:
    """2026-style breakdown with nonzero hubScore is not blank."""
    hub_score_nonzero = {
        "autoCount": 93,
        "totalPoints": 524,
    }
    hub_score_zero = {"autoCount": 0, "totalPoints": 0}
    alliances = {
        "red": MatchAlliance(teams=["frc1", "frc2", "frc3"], score=0),
        "blue": MatchAlliance(teams=["frc4", "frc5", "frc6"], score=0),
    }
    breakdown = {
        "red": {"totalPoints": 0, "hubScore": hub_score_nonzero},
        "blue": {"totalPoints": 0, "hubScore": hub_score_zero},
    }
    match = _make_sf_match(json.dumps(alliances), json.dumps(breakdown))
    assert FMSAPIHybridScheduleParser.is_blank_match(match) is False


def test_is_blank_match_deeply_nested_all_zero() -> None:
    """Arbitrarily nested breakdown with all zeros/blanks is still blank."""
    alliances = {
        "red": MatchAlliance(teams=["frc1", "frc2", "frc3"], score=0),
        "blue": MatchAlliance(teams=["frc4", "frc5", "frc6"], score=0),
    }
    breakdown = {
        "red": {
            "totalPoints": 0,
            "nested": {"level2": {"level3": 0, "level3b": "None"}, "flat": 0},
        },
        "blue": {
            "totalPoints": 0,
            "nested": {"level2": {"level3": 0, "level3b": "None"}, "flat": 0},
        },
    }
    match = _make_sf_match(json.dumps(alliances), json.dumps(breakdown))
    assert FMSAPIHybridScheduleParser.is_blank_match(match) is True


def test_is_blank_match_deeply_nested_nonzero() -> None:
    """A nonzero value buried in arbitrary nesting makes the match non-blank."""
    alliances = {
        "red": MatchAlliance(teams=["frc1", "frc2", "frc3"], score=0),
        "blue": MatchAlliance(teams=["frc4", "frc5", "frc6"], score=0),
    }
    breakdown = {
        "red": {
            "totalPoints": 0,
            "nested": {"level2": {"level3": 42}},
        },
        "blue": {
            "totalPoints": 0,
            "nested": {"level2": {"level3": 0}},
        },
    }
    match = _make_sf_match(json.dumps(alliances), json.dumps(breakdown))
    assert FMSAPIHybridScheduleParser.is_blank_match(match) is False


def test_is_blank_match_nested_dict_with_nonempty_list() -> None:
    """Nested dict containing a non-empty list is not blank and must not raise TypeError."""
    alliances = {
        "red": MatchAlliance(teams=["frc1", "frc2", "frc3"], score=0),
        "blue": MatchAlliance(teams=["frc4", "frc5", "frc6"], score=0),
    }
    breakdown = {
        "red": {
            "totalPoints": 0,
            "hubScore": {"autoCount": 0, "totalPoints": 0, "notes": ["detail"]},
        },
        "blue": {
            "totalPoints": 0,
            "hubScore": {"autoCount": 0, "totalPoints": 0, "notes": []},
        },
    }
    match = _make_sf_match(json.dumps(alliances), json.dumps(breakdown))
    assert FMSAPIHybridScheduleParser.is_blank_match(match) is False


def _put_event(
    event_key: str = "2016nyny",
    year: int = 2016,
    event_short: str = "nyny",
    timezone_id: Optional[str] = "America/New_York",
) -> Event:
    event = Event(
        id=event_key,
        name="Test Event",
        event_type_enum=EventType.REGIONAL,
        short_name="Test",
        event_short=event_short,
        year=year,
        end_date=datetime(year, 3, 27),
        official=True,
        start_date=datetime(year, 3, 24),
        timezone_id=timezone_id,
    )
    event.put()
    return event


def _team(team_number: Optional[int], station: Optional[str]) -> Dict[str, Any]:
    return {
        "teamNumber": team_number,
        "station": station,
        "surrogate": False,
        "dq": False,
    }


def _default_teams() -> List[Dict[str, Any]]:
    return [
        _team(1, "Red1"),
        _team(2, "Red2"),
        _team(3, "Red3"),
        _team(4, "Blue1"),
        _team(5, "Blue2"),
        _team(6, "Blue3"),
    ]


def _schedule_match(
    match_number: int = 1,
    level: str = "Qualification",
    start_time: Optional[str] = "2016-03-13T13:30:00",
    actual_start_time: Optional[str] = None,
    red_score: Optional[int] = 10,
    blue_score: Optional[int] = 20,
    teams: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    return {
        "description": f"Match {match_number}",
        "tournamentLevel": level,
        "matchNumber": match_number,
        "startTime": start_time,
        "actualStartTime": actual_start_time,
        "scoreRedFinal": red_score,
        "scoreBlueFinal": blue_score,
        "Teams": teams if teams is not None else _default_teams(),
    }


def _parse(schedule: List[Dict[str, Any]]) -> Tuple[List[Match], Dict[str, str]]:
    return FMSAPIHybridScheduleParser(2016, "nyny").parse(
        cast(EventScheduleHybridModelV2, {"Schedule": schedule})
    )


def test_parse_event_without_timezone_keeps_naive_time(ndb_stub) -> None:
    """Without a timezone the parser logs a warning and uses the raw API time."""
    _put_event(timezone_id=None)
    matches, _ = _parse([_schedule_match(actual_start_time="2016-03-13T13:36:27.447")])
    assert len(matches) == 1
    assert matches[0].time == datetime(2016, 3, 13, 13, 30, 0)
    assert matches[0].actual_time == datetime(2016, 3, 13, 13, 36, 27)


def test_parse_2015_level_key(ndb_stub) -> None:
    """2015-era responses use `level` instead of `tournamentLevel`."""
    _put_event()
    match = _schedule_match()
    del match["tournamentLevel"]
    match["level"] = "Qualification"
    matches, _ = _parse([match])
    assert len(matches) == 1
    assert matches[0].comp_level == CompLevel.QM
    assert matches[0].key_name == "2016nyny_qm1"


def test_parse_skips_null_team_when_scores_present(ndb_stub) -> None:
    """A null team in a scored match is dropped but the match is still parsed."""
    _put_event()
    teams = _default_teams()
    teams[2] = _team(None, "Red3")
    matches, _ = _parse([_schedule_match(teams=teams)])
    assert len(matches) == 1
    # Teams are sorted by station name, so Blue stations sort before Red.
    assert matches[0].team_key_names == ["frc4", "frc5", "frc6", "frc1", "frc2"]
    assert matches[0].alliances[AllianceColor.RED]["teams"] == ["frc1", "frc2"]
    assert matches[0].alliances[AllianceColor.BLUE]["teams"] == [
        "frc4",
        "frc5",
        "frc6",
    ]


def test_parse_skips_null_team_when_unscored(ndb_stub) -> None:
    """A null team in an unscored match causes the whole match to be skipped."""
    _put_event()
    teams = _default_teams()
    teams[0] = _team(None, "Red1")
    matches, _ = _parse([_schedule_match(teams=teams, red_score=None, blue_score=None)])
    assert matches == []


def test_parse_team_with_null_station(ndb_stub) -> None:
    """A team with a null station is in team_key_names but on neither alliance."""
    _put_event()
    matches, _ = _parse([_schedule_match(teams=[_team(254, None)])])
    assert len(matches) == 1
    assert matches[0].team_key_names == ["frc254"]
    assert matches[0].alliances[AllianceColor.RED]["teams"] == []
    assert matches[0].alliances[AllianceColor.BLUE]["teams"] == []


def test_parse_skips_match_without_start_time(ndb_stub) -> None:
    """Matches with no startTime are unneeded rubber matches and are skipped."""
    _put_event()
    matches, _ = _parse(
        [
            _schedule_match(match_number=1, start_time=None),
            _schedule_match(match_number=2),
        ]
    )
    assert [m.key_name for m in matches] == ["2016nyny_qm2"]


def test_parse_corrupt_existing_match_skips_tiebreak_logic(
    ndb_stub, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An existing match with no alliances_json is ignored for tiebreak purposes."""
    event = _put_event()
    # alliances_json is a required property, so such a corrupt entity can only
    # come from legacy data. Simulate it by returning an unsaved Match.
    corrupt = Match(
        id="2016nyny_qm1",
        event=event.key,
        year=2016,
        comp_level=CompLevel.QM,
        set_number=1,
        match_number=1,
    )
    monkeypatch.setattr(Match, "get_by_id", classmethod(lambda cls, _key: corrupt))

    matches, remapped = _parse([_schedule_match()])
    assert remapped == {}
    assert len(matches) == 1
    assert matches[0].key_name == "2016nyny_qm1"
    assert matches[0].alliances[AllianceColor.RED]["score"] == 10
    assert matches[0].alliances[AllianceColor.BLUE]["score"] == 20


def test_parse_tied_match_with_too_few_matches_is_skipped(ndb_stub) -> None:
    """
    In a classic bracket a tiebreaker can only follow at least 3 matches in the
    set. If a tie is detected earlier, the parser warns and drops the match.
    """
    event = _put_event()
    played_at = datetime(2016, 3, 13, 18, 0, 0)
    Match(
        id="2016nyny_sf1m1",
        event=event.key,
        year=2016,
        comp_level=CompLevel.SF,
        set_number=1,
        match_number=1,
        team_key_names=["frc1", "frc2", "frc3", "frc4", "frc5", "frc6"],
        actual_time=played_at,
        alliances_json=json.dumps(
            {
                "red": MatchAlliance(teams=["frc1", "frc2", "frc3"], score=100),
                "blue": MatchAlliance(teams=["frc4", "frc5", "frc6"], score=100),
            }
        ),
    ).put()

    # Match 13 is sf1m1 in an 8 team bracket. A different actual time means
    # the API is describing a new (tiebreaker) match for the same slot.
    matches, remapped = _parse(
        [
            _schedule_match(
                match_number=13,
                level="Playoff",
                actual_start_time="2016-03-13T14:15:00.000",
                red_score=50,
                blue_score=60,
            )
        ]
    )
    assert matches == []
    assert remapped == {}
