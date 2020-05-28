import json

import unittest2

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from datafeeds.parsers.fms_api.fms_api_event_alliances_parser import FMSAPIEventAlliancesParser


class TestFMSAPIEventListParser(unittest2.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

    def tearDown(self):
        self.testbed.deactivate()

    def test_parse_no_alliances(self):
        with open('test_data/fms_api/2016_no_alliances.json', 'r') as f:
            alliances = FMSAPIEventAlliancesParser().parse(json.loads(f.read()))

            self.assertIsNone(alliances)

    def test_parse_8alliances(self):
        with open('test_data/fms_api/2016_nyny_alliances.json', 'r') as f:
            alliances = FMSAPIEventAlliancesParser().parse(json.loads(f.read()))

            self.assertTrue(isinstance(alliances, list))
            self.assertEqual(len(alliances), 8)

            # Ensure that we have the alliances in the proper order and that backup teams propegate
            number = 1
            for alliance in alliances:
                self.assertEqual(alliance['name'], 'Alliance {}'.format(number))
                self.assertIsNone(alliance['backup'])
                number += 1

    def test_parse_16alliances(self):
        with open('test_data/fms_api/2016_micmp_alliances_staging.json', 'r') as f:
            alliances = FMSAPIEventAlliancesParser().parse(json.loads(f.read()))

            self.assertTrue(isinstance(alliances, list))
            self.assertEqual(len(alliances), 16)

            number = 1
            for alliance in alliances:
                self.assertEqual(alliance['name'], 'Alliance {}'.format(number))
                self.assertIsNone(alliance['backup'])
                number += 1

    def test_parse_4team(self):
        with open('test_data/fms_api/2015_curie_alliances.json', 'r') as f:
            alliances = FMSAPIEventAlliancesParser().parse(json.loads(f.read()))

            self.assertTrue(isinstance(alliances, list))
            self.assertEqual(len(alliances), 8)

            number = 1
            for alliance in alliances:
                self.assertEqual(alliance['name'], 'Alliance {}'.format(number))
                self.assertIsNone(alliance['backup'])
                number += 1

    def test_parse_backup_team_used(self):
        with open('test_data/fms_api/2016_necmp_alliances.json', 'r') as f:
            alliances = FMSAPIEventAlliancesParser().parse(json.loads(f.read()))

            self.assertTrue(isinstance(alliances, list))
            self.assertEqual(len(alliances), 8)

            number = 1
            for alliance in alliances:
                self.assertEqual(alliance['name'], 'Alliance {}'.format(number))
                if number == 5:
                    self.assertIsNotNone(alliance['backup'])
                    self.assertEqual(alliance['backup']['in'], 'frc4905')
                    self.assertEqual(alliance['backup']['out'], 'frc999')
                else:
                    self.assertIsNone(alliance['backup'])
                number += 1

    def test_parse_ignore_no_picks(self):
        with open('test_data/fms_api/2019_ohwa2_alliances.json', 'r') as f:
            alliances = FMSAPIEventAlliancesParser().parse(json.loads(f.read()))

            self.assertTrue(isinstance(alliances, list))
            self.assertEqual(len(alliances), 7)
