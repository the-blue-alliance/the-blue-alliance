import json
from datetime import datetime

import pytest

from backend.common.consts.alliance_color import AllianceColor
from backend.common.consts.comp_level import CompLevel
from backend.common.consts.event_type import EventType
from backend.common.consts.playoff_type import PlayoffType
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
