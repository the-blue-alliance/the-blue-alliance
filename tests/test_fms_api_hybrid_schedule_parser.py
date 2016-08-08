import json
from datetime import datetime

import unittest2

from google.appengine.ext import testbed

from consts.event_type import EventType
from datafeeds.parsers.fms_api.fms_api_match_parser import FMSAPIHybridScheduleParser
from helpers.match_helper import MatchHelper
from models.event import Event


class TestFMSAPIEventListParser(unittest2.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()

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
            matches = FMSAPIHybridScheduleParser(2016, 'nyny').parse(json.loads(f.read()))

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
            matches = FMSAPIHybridScheduleParser(2016, 'nyny').parse(json.loads(f.read()))

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
            matches = FMSAPIHybridScheduleParser(2016, 'nyny').parse(json.loads(f.read()))

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
                timezone_id="America/New_York"
        )
        self.event.put()

        with open('test_data/fms_api/2016_micmp_staging_hybrid_schedule_playoff.json', 'r') as f:
            matches = FMSAPIHybridScheduleParser(2016, 'micmp').parse(json.loads(f.read()))

            self.assertTrue(isinstance(matches, list))

            self.assertEquals(len(matches), 36)

            # Assert we get enough of each match type
            clean_matches = MatchHelper.organizeMatches(matches)
            self.assertEqual(len(clean_matches["ef"]), 20)
            self.assertEqual(len(clean_matches["qf"]), 10)
            self.assertEqual(len(clean_matches["sf"]), 4)
            self.assertEqual(len(clean_matches["f"]), 2)
