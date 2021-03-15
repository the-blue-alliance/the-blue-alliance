import datetime
import json
import unittest2

from consts.event_type import EventType

from datafeeds.parsers.fms_api.fms_api_awards_parser import FMSAPIAwardsParser
from datafeeds.parsers.fms_api.fms_api_event_alliances_parser import FMSAPIEventAlliancesParser
from datafeeds.parsers.fms_api.fms_api_event_rankings_parser import FMSAPIEventRankingsParser
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

    def test_parseAwards(self):
        with open('test_data/fms_api/2015waamv_staging_awards.json', 'r') as f:
            awards = FMSAPIAwardsParser(self.event).parse(json.loads(f.read()))

        self.assertEqual(len(awards), 5)

        for award in awards:
            if award.key.id() == '2015waamv_3':
                self.assertEqual(award.name_str, 'Woodie Flowers Award')
                self.assertEqual(award.award_type_enum, 3)
                self.assertTrue({'team_number': None, 'awardee': 'Bob'} in award.recipient_list)
            elif award.key.id() == '2015waamv_17':
                self.assertEqual(award.name_str, 'Quality Award sponsored by Motorola')
                self.assertEqual(award.award_type_enum, 17)
                self.assertTrue({'team_number': 1318, 'awardee': None} in award.recipient_list)
            elif award.key.id() == '2015waamv_4':
                self.assertEqual(award.name_str, 'FIRST Dean\'s List Award')
                self.assertEqual(award.award_type_enum, 4)
                self.assertTrue({'team_number': 123, 'awardee': 'Person Name 1'} in award.recipient_list)
                self.assertTrue({'team_number': 321, 'awardee': 'Person Name 2'} in award.recipient_list)

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

    def test_parseEventRankings(self):
        with open('test_data/fms_api/2015waamv_staging_rankings.json', 'r') as f:
            rankings = FMSAPIEventRankingsParser(2015).parse(json.loads(f.read()))

        self.assertEqual(rankings,
                         [['Rank', 'Team', 'Qual Avg', 'Auto', 'Container', 'Coopertition', 'Litter', 'Tote', 'Played'],
                          [1, 2906, 76, 6, 48, 80, 6, 12, 2],
                          [2, 4726, 74, 6, 48, 80, 6, 8, 2],
                          [3, 2929, 70, 6, 48, 80, 6, 0, 2],
                          [4, 2907, 59, 14, 0, 40, 0, 64, 2],
                          [5, 2046, 58, 14, 24, 20, 4, 60, 2],
                          [6, 1294, 54, 14, 0, 40, 0, 60, 2],
                          [7, 360, 51, 0, 48, 20, 12, 22, 2],
                          [8, 3218, 50, 18, 12, 40, 4, 26, 2],
                          [9, 3237, 48, 18, 12, 0, 4, 14, 1],
                          [10, 3781, 46, 46, 20, 20, 6, 0, 1],
                          [11, 3393, 46, 46, 20, 20, 6, 0, 1],
                          [12, 1983, 46, 14, 0, 0, 4, 80, 2],
                          [13, 4579, 44, 0, 24, 60, 4, 0, 2],
                          [14, 3220, 44, 18, 12, 40, 4, 14, 2],
                          [15, 3049, 44, 0, 0, 40, 4, 0, 1],
                          [16, 5295, 43, 22, 0, 0, 0, 70, 2],
                          [17, 4131, 43, 14, 28, 0, 6, 38, 2],
                          [18, 4911, 38, 0, 0, 40, 0, 36, 2],
                          [19, 2605, 36, 0, 28, 0, 10, 34, 2],
                          [20, 3586, 34, 20, 0, 0, 0, 60, 2],
                          [21, 2976, 33, 8, 0, 40, 0, 18, 2],
                          [22, 3684, 29, 8, 0, 40, 0, 10, 2],
                          [23, 3223, 28, 0, 0, 40, 4, 12, 2],
                          [24, 3588, 27, 0, 0, 0, 4, 56, 2],
                          [25, 4450, 24, 0, 24, 20, 4, 0, 2],
                          [26, 2927, 22, 0, 0, 40, 4, 0, 2],
                          [27, 2412, 22, 0, 0, 40, 4, 0, 2],
                          [28, 3221, 21, 0, 0, 0, 8, 40, 2],
                          [29, 3663, 15, 14, 0, 0, 0, 16, 2],
                          [30, 4469, 15, 14, 0, 0, 0, 16, 2],
                          [31, 2557, 15, 6, 0, 0, 0, 36, 2],
                          [32, 1318, 1, 6, 0, 0, 0, 8, 2]])

    def test_parse2017Awards(self):
        self.event = Event(
            id="2017cmpmo",
            end_date=datetime.datetime(2017, 4, 29, 0, 0),
            event_short="cmpmo",
            event_type_enum=EventType.CMP_FINALS,
            district_key=None,
            first_eid="22465",
            name="Einstein Field (St. Louis)",
            start_date=datetime.datetime(2017, 4, 29, 0, 0),
            year=2017,
            timezone_id='America/Chicago'
        )
        self.event.put()

        with open('test_data/fms_api/2017cmpmo_awards.json', 'r') as f:
            awards = FMSAPIAwardsParser(self.event).parse(json.loads(f.read()))

        self.assertEqual(len(awards), 6)

        for award in awards:
            if award.key.id() == '2017cmpmo_0':
                self.assertEqual(award.name_str, 'Chairman\'s Award')
                self.assertEqual(award.award_type_enum, 0)
                self.assertFalse({'team_number': 2169, 'awardee': None} in award.recipient_list)
                self.assertFalse({'team_number': 1885, 'awardee': None} in award.recipient_list)
                self.assertTrue({'team_number': 2614, 'awardee': None} in award.recipient_list)
            elif award.key.id() == '2017cmpmo_69':
                self.assertEqual(award.name_str, 'Chairman\'s Award Finalist')
                self.assertEqual(award.award_type_enum, 69)
                self.assertTrue({'team_number': 2169, 'awardee': None} in award.recipient_list)
                self.assertTrue({'team_number': 1885, 'awardee': None} in award.recipient_list)
                self.assertFalse({'team_number': 2614, 'awardee': None} in award.recipient_list)
