import datetime
import json
import unittest2

from consts.event_type import EventType

from datafeeds.parsers.fms_api.fms_api_event_alliances_parser import FMSAPIEventAlliancesParser
from datafeeds.parsers.fms_api.fms_api_match_parser import FMSAPIHybridScheduleParser

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from models.event import Event


class TestFMSAPIEventParser(unittest2.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        self.event = Event(
            id="2015waamv",
            end_date=datetime.datetime(2015, 4, 2, 0, 0),
            event_short="waamv",
            event_type_enum=EventType.REGIONAL,
            district_key=None,
            first_eid="13467",
            name="PNW District - Auburn Mountainview Event",
            start_date=datetime.datetime(2015, 3, 31, 0, 0),
            year=2015,
            timezone_id='America/Los_Angeles'
        )
        self.event.put()

    def tearDown(self):
        self.testbed.deactivate()

    def test_parseMatches(self):
        with open('test_data/fms_api/2015waamv_staging_matches.json', 'r') as f:
            matches, _ = FMSAPIHybridScheduleParser(2015, 'waamv').parse(json.loads(f.read()))

        self.assertEqual(len(matches), 64)

        matches = sorted(matches, key=lambda m: m.play_order)

        # Test played match
        match = matches[0]
        self.assertEqual(match.comp_level, "qm")
        self.assertEqual(match.set_number, 1)
        self.assertEqual(match.match_number, 1)
        self.assertEqual(match.team_key_names, [u'frc4131', u'frc4469', u'frc3663', u'frc3684', u'frc5295', u'frc2976'])
        self.assertEqual(match.alliances_json, """{"blue": {"dqs": [], "surrogates": [], "score": 30, "teams": ["frc4131", "frc4469", "frc3663"]}, "red": {"dqs": [], "surrogates": [], "score": 18, "teams": ["frc3684", "frc5295", "frc2976"]}}""")
        self.assertEqual(match.time, datetime.datetime(2015, 2, 27, 0, 0))
        self.assertEqual(match.actual_time, datetime.datetime(2015, 2, 27, 0, 0))

        # Test unplayed match
        match = matches[11]
        self.assertEqual(match.comp_level, "qm")
        self.assertEqual(match.set_number, 1)
        self.assertEqual(match.match_number, 12)
        self.assertEqual(match.team_key_names, [u'frc3663', u'frc5295', u'frc2907', u'frc2046', u'frc3218', u'frc2412'])
        self.assertEqual(match.alliances_json, """{"blue": {"dqs": [], "surrogates": [], "score": null, "teams": ["frc3663", "frc5295", "frc2907"]}, "red": {"dqs": [], "surrogates": [], "score": null, "teams": ["frc2046", "frc3218", "frc2412"]}}""")
        self.assertEqual(match.time, datetime.datetime(2015, 2, 27, 2, 17))
        self.assertEqual(match.actual_time, None)

    def test_parseEventAlliances(self):
        with open('test_data/fms_api/2015waamv_staging_alliances.json', 'r') as f:
            alliances = FMSAPIEventAlliancesParser().parse(json.loads(f.read()))

        self.assertEqual(alliances,
                         [{'declines': [], 'picks': ['frc1', 'frc2', 'frc3'], 'backup': None, 'name': 'Alliance 1'},
                          {'declines': [], 'picks': ['frc5', 'frc6', 'frc7', 'frc8'], 'backup': None, 'name': 'Alliance 2'},
                          {'declines': [], 'picks': ['frc9', 'frc10', 'frc11', 'frc12'], 'backup': None, 'name': 'Alliance 3'},
                          {'declines': [], 'picks': ['frc13', 'frc14', 'frc15', 'frc16'], 'backup': None, 'name': 'Alliance 4'},
                          {'declines': [], 'picks': ['frc17', 'frc18', 'frc19', 'frc20'], 'backup': None, 'name': 'Alliance 5'},
                          {'declines': [], 'picks': ['frc21', 'frc22', 'frc23', 'frc24'], 'backup': None, 'name': 'Alliance 6'},
                          {'declines': [], 'picks': ['frc25', 'frc26', 'frc27', 'frc28'], 'backup': None, 'name': 'Alliance 7'},
                          {'declines': [], 'picks': ['frc29', 'frc30', 'frc31', 'frc31'], 'backup': None, 'name': 'Alliance 8'}])
