import json
from datetime import datetime

from backend.common.consts.comp_level import CompLevel
from backend.common.consts.event_type import EventType
from backend.common.consts.playoff_type import PlayoffType
from backend.common.helpers.match_helper import MatchHelper
from backend.common.models.event import Event
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
