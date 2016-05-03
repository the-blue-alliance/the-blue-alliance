import json

import unittest2

from google.appengine.ext import testbed

from datafeeds.parsers.fms_api.fms_api_event_alliances_parser import FMSAPIEventAlliancesParser


class TestFMSAPIEventListParser(unittest2.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()

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

    def test_parse_16alliances(self):
        with open('test_data/fms_api/2016_micmp_alliances_staging.json', 'r') as f:
            alliances = FMSAPIEventAlliancesParser().parse(json.loads(f.read()))

            self.assertTrue(isinstance(alliances, list))
            self.assertEqual(len(alliances), 16)

    def test_parse_4team(self):
        with open('test_data/fms_api/2015_curie_alliances.json', 'r') as f:
            alliances = FMSAPIEventAlliancesParser().parse(json.loads(f.read()))

            self.assertTrue(isinstance(alliances, list))
            self.assertEqual(len(alliances), 8)