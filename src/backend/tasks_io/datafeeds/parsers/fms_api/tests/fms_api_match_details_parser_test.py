import json
from datetime import datetime
from typing import Any, cast, Dict, List

import pytest

from backend.common.consts.alliance_color import AllianceColor
from backend.common.consts.comp_level import CompLevel
from backend.common.consts.event_type import EventType
from backend.common.consts.playoff_type import PlayoffType
from backend.common.frc_api.frc_api import TScoreDetailReturn
from backend.common.helpers.match_helper import MatchHelper
from backend.common.models.event import Event
from backend.tasks_io.datafeeds.parsers.fms_api.fms_api_match_parser import (
    FMSAPIMatchDetailsParser,
)


@pytest.fixture(autouse=True)
def setUp(ndb_stub):
    event_nyny = Event(
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
    event_nyny.put()

    event_micmp = Event(
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
    event_micmp.put()

    event_2018week0 = Event(
        id="2018week0",
        name="Week 0",
        event_type_enum=EventType.PRESEASON,
        short_name="Week 0",
        event_short="week0",
        year=2018,
        end_date=datetime(2018, 2, 17),
        official=True,
        start_date=datetime(2018, 2, 17),
        timezone_id="America/New_York",
        playoff_type=PlayoffType.BRACKET_8_TEAM,
    )
    event_2018week0.put()


def test_parse_no_matches(test_data_importer) -> None:
    path = test_data_importer._get_path(__file__, "data/2016_no_score_breakdown.json")
    with open(path, "r") as f:
        matches = FMSAPIMatchDetailsParser(2016, "nyny").parse(json.loads(f.read()))

        assert isinstance(matches, dict)
        assert len(matches) == 0


def test_parse_qual(test_data_importer) -> None:
    path = test_data_importer._get_path(__file__, "data/2016_nyny_qual_breakdown.json")
    with open(path, "r") as f:
        matches = FMSAPIMatchDetailsParser(2016, "nyny").parse(json.loads(f.read()))

        assert isinstance(matches, dict)
        assert len(matches) == 88

        # Assert we get enough of each match type
        _, clean_matches = MatchHelper.organized_keys(list(matches.keys()))
        assert len(clean_matches[CompLevel.QM]) == 88

    # Changed format in 2018
    path = test_data_importer._get_path(
        __file__, "data/2016_nyny_qual_breakdown_2018update.json"
    )
    with open(path, "r") as f:
        matches = FMSAPIMatchDetailsParser(2016, "nyny").parse(json.loads(f.read()))

        assert isinstance(matches, dict)
        assert len(matches) == 88

        # Assert we get enough of each match type
        _, clean_matches = MatchHelper.organized_keys(list(matches.keys()))
        assert len(clean_matches[CompLevel.QM]) == 88


def test_parse_qual_2018(test_data_importer) -> None:
    path = test_data_importer._get_path(__file__, "data/2018_week0_qual_breakdown.json")
    with open(path, "r") as f:
        matches = FMSAPIMatchDetailsParser(2018, "week0").parse(json.loads(f.read()))

        assert isinstance(matches, dict)
        assert len(matches) == 13

        # Assert we get enough of each match type
        _, clean_matches = MatchHelper.organized_keys(list(matches.keys()))
        assert len(clean_matches[CompLevel.QM]) == 13

        # Test gameData
        assert matches["2018week0_qm1"][AllianceColor.RED]["tba_gameData"] == "LRL"
        assert matches["2018week0_qm1"][AllianceColor.BLUE]["tba_gameData"] == "LRL"
        assert matches["2018week0_qm3"][AllianceColor.RED]["tba_gameData"] == "RRR"
        assert matches["2018week0_qm3"][AllianceColor.BLUE]["tba_gameData"] == "RRR"
        assert matches["2018week0_qm4"][AllianceColor.RED]["tba_gameData"] == "RLR"
        assert matches["2018week0_qm4"][AllianceColor.BLUE]["tba_gameData"] == "RLR"
        assert matches["2018week0_qm8"][AllianceColor.RED]["tba_gameData"] == "LLL"
        assert matches["2018week0_qm8"][AllianceColor.BLUE]["tba_gameData"] == "LLL"


def test_parse_playoff(test_data_importer) -> None:
    path = test_data_importer._get_path(
        __file__, "data/2016_nyny_playoff_breakdown.json"
    )
    with open(path, "r") as f:
        matches = FMSAPIMatchDetailsParser(2016, "nyny").parse(json.loads(f.read()))

        assert isinstance(matches, dict)
        assert len(matches) == 15

        # Assert we get enough of each match type
        _, clean_matches = MatchHelper.organized_keys(list(matches.keys()))
        assert len(clean_matches[CompLevel.EF]) == 0
        assert len(clean_matches[CompLevel.QF]) == 9
        assert len(clean_matches[CompLevel.SF]) == 4
        assert len(clean_matches[CompLevel.F]) == 2


def test_parse_playoff_with_octofinals(test_data_importer) -> None:
    path = test_data_importer._get_path(
        __file__, "data/2016_micmp_staging_playoff_breakdown.json"
    )
    with open(path, "r") as f:
        matches = FMSAPIMatchDetailsParser(2016, "micmp").parse(json.loads(f.read()))

        assert isinstance(matches, dict)
        assert len(matches) == 36

        # Assert we get enough of each match type
        _, clean_matches = MatchHelper.organized_keys(list(matches.keys()))
        assert len(clean_matches[CompLevel.EF]) == 20
        assert len(clean_matches[CompLevel.QF]) == 10
        assert len(clean_matches[CompLevel.SF]) == 4
        assert len(clean_matches[CompLevel.F]) == 2


def _put_event(year: int, event_short: str, playoff_type: PlayoffType) -> None:
    Event(
        id=f"{year}{event_short}",
        name="Test Event",
        event_type_enum=EventType.REGIONAL,
        short_name="Test",
        event_short=event_short,
        year=year,
        end_date=datetime(year, 3, 27),
        official=True,
        start_date=datetime(year, 3, 24),
        timezone_id="America/New_York",
        playoff_type=playoff_type,
    ).put()


def _parse(
    year: int, event_short: str, matches: List[Dict[str, Any]]
) -> Dict[str, Any]:
    return FMSAPIMatchDetailsParser(year, event_short).parse(
        cast(TScoreDetailReturn, {"MatchScores": matches})
    )


def test_parse_2015_coopertition() -> None:
    """2015 responses carry top-level coopertition fields onto the breakdown."""
    _put_event(2015, "nyny", PlayoffType.AVG_SCORE_8_TEAM)
    breakdowns = _parse(
        2015,
        "nyny",
        [
            {
                "matchLevel": "Qualification",
                "matchNumber": 1,
                "coopertition": "Stack",
                "coopertitionPoints": 40,
                "Alliances": [
                    {"alliance": "Red", "totalPoints": 50},
                    {"alliance": "Blue", "totalPoints": 60},
                ],
            }
        ],
    )
    breakdown = breakdowns["2015nyny_qm1"]
    assert breakdown["coopertition"] == "Stack"
    assert breakdown["coopertition_points"] == 40
    assert breakdown[AllianceColor.RED] == {"totalPoints": 50}
    assert breakdown[AllianceColor.BLUE] == {"totalPoints": 60}


def test_parse_2024_copies_bonus_thresholds_to_each_alliance() -> None:
    """2024 bonus thresholds live on the match and are duplicated per alliance."""
    _put_event(2024, "nyny", PlayoffType.DOUBLE_ELIM_8_TEAM)
    breakdowns = _parse(
        2024,
        "nyny",
        [
            {
                "matchLevel": "Qualification",
                "matchNumber": 3,
                "coopertitionBonusAchieved": True,
                "melodyBonusThresholdCoop": 15,
                "melodyBonusThresholdNonCoop": 18,
                "melodyBonusThreshold": 15,
                "ensembleBonusStagePointsThreshold": 10,
                "ensembleBonusOnStageRobotsThreshold": 2,
                "alliances": [
                    {"alliance": "Red", "totalPoints": 70},
                    {"alliance": "Blue", "totalPoints": 65},
                ],
            }
        ],
    )
    breakdown = breakdowns["2024nyny_qm3"]
    for color, total in [(AllianceColor.RED, 70), (AllianceColor.BLUE, 65)]:
        assert breakdown[color] == {
            "coopertitionBonusAchieved": True,
            "melodyBonusThresholdCoop": 15,
            "melodyBonusThresholdNonCoop": 18,
            "melodyBonusThreshold": 15,
            "ensembleBonusStagePointsThreshold": 10,
            "ensembleBonusOnStageRobotsThreshold": 2,
            "totalPoints": total,
        }


def _rocket_fields(near_complete: bool, far_complete: bool) -> Dict[str, Any]:
    fields: Dict[str, Any] = {}
    for side, complete in [("Near", near_complete), ("Far", far_complete)]:
        for level in ["low", "mid", "top"]:
            for side2 in ["Left", "Right"]:
                fields[f"{level}{side2}Rocket{side}"] = "PanelAndCargo"
        if not complete:
            fields[f"topRightRocket{side}"] = "Panel"
    return fields


def test_parse_2019_derives_completed_rockets() -> None:
    """2019 completedRocket flags are recomputed from the individual bays."""
    _put_event(2019, "nyny", PlayoffType.BRACKET_8_TEAM)
    red = {"alliance": "Red", "completedRocketNear": False, "completedRocketFar": True}
    red.update(_rocket_fields(near_complete=True, far_complete=False))
    blue = {"alliance": "Blue", "completedRocketNear": True, "completedRocketFar": True}
    blue.update(_rocket_fields(near_complete=False, far_complete=False))
    breakdowns = _parse(
        2019,
        "nyny",
        [
            {
                "matchLevel": "Qualification",
                "matchNumber": 7,
                "alliances": [red, blue],
            }
        ],
    )
    breakdown = breakdowns["2019nyny_qm7"]
    assert breakdown[AllianceColor.RED]["completedRocketNear"] is True
    assert breakdown[AllianceColor.RED]["completedRocketFar"] is False
    assert breakdown[AllianceColor.BLUE]["completedRocketNear"] is False
    assert breakdown[AllianceColor.BLUE]["completedRocketFar"] is False
