import json
from datetime import datetime

import unittest2

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from consts.event_type import EventType
from consts.playoff_type import PlayoffType
from datafeeds.parsers.fms_api.fms_api_match_parser import FMSAPIHybridScheduleParser
from helpers.match_helper import MatchHelper
from models.event import Event


class TestFMSAPIEventListParser(unittest2.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

    def tearDown(self):
        self.testbed.deactivate()

    def test_parse_no_matches(self):
        self.event = Event(
            id="2016nyny",
            name="NYC Regional",
            event_type_enum=EventType.REGIONAL,
            short_name="NYC",
            event_short="nyny",
            year=2016,
            end_date=datetime(2016, 03, 27),
            official=True,
            start_date=datetime(2016, 03, 24),
            timezone_id="America/New_York"
        )
        self.event.put()
        with open('test_data/fms_api/2016_hybrid_schedule_no_matches.json', 'r') as f:
            matches, _ = FMSAPIHybridScheduleParser(2016, 'nyny').parse(json.loads(f.read()))

            self.assertTrue(isinstance(matches, list))
            self.assertEqual(len(matches), 0)

    def test_parse_qual(self):
        self.event = Event(
            id="2016nyny",
            name="NYC Regional",
            event_type_enum=EventType.REGIONAL,
            short_name="NYC",
            event_short="nyny",
            year=2016,
            end_date=datetime(2016, 03, 27),
            official=True,
            start_date=datetime(2016, 03, 24),
            timezone_id="America/New_York"
        )
        self.event.put()
        with open('test_data/fms_api/2016_nyny_hybrid_schedule_qual.json', 'r') as f:
            matches, _ = FMSAPIHybridScheduleParser(2016, 'nyny').parse(json.loads(f.read()))

            self.assertTrue(isinstance(matches, list))
            self.assertEqual(len(matches), 88)

            # Assert we get enough of each match type
            clean_matches = MatchHelper.organizeMatches(matches)
            self.assertEqual(len(clean_matches["qm"]), 88)

        # Changed format in 2018
        with open('test_data/fms_api/2016_nyny_hybrid_schedule_qual_2018update.json', 'r') as f:
            matches, _ = FMSAPIHybridScheduleParser(2016, 'nyny').parse(json.loads(f.read()))

            self.assertTrue(isinstance(matches, list))
            self.assertEqual(len(matches), 88)

            # Assert we get enough of each match type
            clean_matches = MatchHelper.organizeMatches(matches)
            self.assertEqual(len(clean_matches["qm"]), 88)

    def test_parse_playoff(self):
        self.event = Event(
            id="2016nyny",
            name="NYC Regional",
            event_type_enum=EventType.REGIONAL,
            short_name="NYC",
            event_short="nyny",
            year=2016,
            end_date=datetime(2016, 03, 27),
            official=True,
            start_date=datetime(2016, 03, 24),
            timezone_id="America/New_York"
        )
        self.event.put()
        with open('test_data/fms_api/2016_nyny_hybrid_schedule_playoff.json', 'r') as f:
            matches, _ = FMSAPIHybridScheduleParser(2016, 'nyny').parse(json.loads(f.read()))

            self.assertTrue(isinstance(matches, list))
            self.assertEqual(len(matches), 15)

            # Assert we get enough of each match type
            clean_matches = MatchHelper.organizeMatches(matches)
            self.assertEqual(len(clean_matches["ef"]), 0)
            self.assertEqual(len(clean_matches["qf"]), 9)
            self.assertEqual(len(clean_matches["sf"]), 4)
            self.assertEqual(len(clean_matches["f"]), 2)

    def test_parse_playoff_with_octofinals(self):
        self.event = Event(
            id="2016micmp",
            name="Michigan District Champs",
            event_type_enum=EventType.DISTRICT_CMP,
            short_name="Michigan",
            event_short="micmp",
            year=2016,
            end_date=datetime(2016, 03, 27),
            official=True,
            start_date=datetime(2016, 03, 24),
            timezone_id="America/New_York",
            playoff_type=PlayoffType.BRACKET_16_TEAM
        )
        self.event.put()

        with open('test_data/fms_api/2016_micmp_staging_hybrid_schedule_playoff.json', 'r') as f:
            matches, _ = FMSAPIHybridScheduleParser(2016, 'micmp').parse(json.loads(f.read()))

            self.assertTrue(isinstance(matches, list))

            self.assertEquals(len(matches), 36)

            # Assert we get enough of each match type
            clean_matches = MatchHelper.organizeMatches(matches)
            self.assertEqual(len(clean_matches["ef"]), 20)
            self.assertEqual(len(clean_matches["qf"]), 10)
            self.assertEqual(len(clean_matches["sf"]), 4)
            self.assertEqual(len(clean_matches["f"]), 2)

    def test_parse_2015_playoff(self):
        self.event = Event(
            id="2015nyny",
            name="NYC Regional",
            event_type_enum=EventType.REGIONAL,
            short_name="NYC",
            event_short="nyny",
            year=2015,
            end_date=datetime(2015, 03, 27),
            official=True,
            start_date=datetime(2015, 03, 24),
            timezone_id="America/New_York",
            playoff_type=PlayoffType.AVG_SCORE_8_TEAM
        )
        self.event.put()
        with open('test_data/fms_api/2015nyny_hybrid_schedule_playoff.json', 'r') as f:
            matches, _ = FMSAPIHybridScheduleParser(2015, 'nyny').parse(json.loads(f.read()))

            self.assertTrue(isinstance(matches, list))
            self.assertEqual(len(matches), 17)

            # Assert we get enough of each match type
            clean_matches = MatchHelper.organizeMatches(matches)
            self.assertEqual(len(clean_matches["ef"]), 0)
            self.assertEqual(len(clean_matches["qf"]), 8)
            self.assertEqual(len(clean_matches["sf"]), 6)
            self.assertEqual(len(clean_matches["f"]), 3)

    def test_parse_2017micmp(self):
        # 2017micmp is a 4 team bracket that starts playoff match numbering at 1
        self.event = Event(
            id="2017micmp",
            name="Michigan District Champs",
            event_type_enum=EventType.DISTRICT_CMP,
            short_name="Michigan",
            event_short="micmp",
            year=2017,
            end_date=datetime(2017, 03, 27),
            official=True,
            start_date=datetime(2017, 03, 24),
            timezone_id="America/New_York",
            playoff_type=PlayoffType.BRACKET_4_TEAM
        )
        self.event.put()

        with open('test_data/fms_api/2017micmp_playoff_schedule.json', 'r') as f:
            matches, _ = FMSAPIHybridScheduleParser(2017, 'micmp').parse(json.loads(f.read()))

            self.assertTrue(isinstance(matches, list))

            self.assertEquals(len(matches), 6)

            # Assert we get enough of each match type
            clean_matches = MatchHelper.organizeMatches(matches)
            self.assertEqual(len(clean_matches["ef"]), 0)
            self.assertEqual(len(clean_matches["qf"]), 0)
            self.assertEqual(len(clean_matches["sf"]), 4)
            self.assertEqual(len(clean_matches["f"]), 2)

    def test_parse_2champs_einstein(self):
        self.event = Event(
            id="2017cmptx",
            name="Einstein (Houston)",
            event_type_enum=EventType.CMP_FINALS,
            short_name="Einstein",
            event_short="cmptx",
            year=2017,
            end_date=datetime(2017, 03, 27),
            official=True,
            start_date=datetime(2017, 03, 24),
            timezone_id="America/New_York",
            playoff_type=PlayoffType.ROUND_ROBIN_6_TEAM
        )
        self.event.put()

        with open('test_data/fms_api/2017cmptx_staging_playoff_schedule.json', 'r') as f:
            matches, _ = FMSAPIHybridScheduleParser(2017, 'cmptx').parse(json.loads(f.read()))

            self.assertTrue(isinstance(matches, list))

            self.assertEquals(len(matches), 18)

            # Assert we get enough of each match type
            clean_matches = MatchHelper.organizeMatches(matches)
            self.assertEqual(len(clean_matches["ef"]), 0)
            self.assertEqual(len(clean_matches["qf"]), 0)
            self.assertEqual(len(clean_matches["sf"]), 15)
            self.assertEqual(len(clean_matches["f"]), 3)

    def test_parse_foc_b05(self):
        self.event = Event(
            id="2017nhfoc",
            name="FIRST Festival of Champions",
            event_type_enum=EventType.CMP_FINALS,
            short_name="FIRST Festival of Champions",
            event_short="nhfoc",
            first_code="foc",
            year=2017,
            end_date=datetime(2017, 07, 29),
            official=True,
            start_date=datetime(2017, 07, 29),
            timezone_id="America/New_York",
            playoff_type=PlayoffType.BO5_FINALS
        )
        self.event.put()

        with open('test_data/fms_api/2017foc_staging_hybrid_schedule_playoff.json', 'r') as f:
            matches, _ = FMSAPIHybridScheduleParser(2017, 'nhfoc').parse(json.loads(f.read()))

            self.assertTrue(isinstance(matches, list))

            self.assertEquals(len(matches), 5)

            # Assert we get enough of each match type
            clean_matches = MatchHelper.organizeMatches(matches)
            self.assertEqual(len(clean_matches["ef"]), 0)
            self.assertEqual(len(clean_matches["qf"]), 0)
            self.assertEqual(len(clean_matches["sf"]), 0)
            self.assertEqual(len(clean_matches["f"]), 5)

            for i, match in enumerate(clean_matches['f']):
                self.assertEqual(match.set_number, 1)
                self.assertEqual(match.match_number, i+1)
