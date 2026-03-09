import json
from datetime import datetime

from backend.common.consts.comp_level import CompLevel
from backend.common.consts.event_type import EventType
from backend.common.consts.playoff_type import PlayoffType
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
