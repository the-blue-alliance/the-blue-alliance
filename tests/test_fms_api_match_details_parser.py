import json
from datetime import datetime

import unittest2

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from datafeeds.parsers.fms_api.fms_api_match_parser import FMSAPIMatchDetailsParser


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
        with open('test_data/fms_api/2016_no_score_breakdown.json', 'r') as f:
            matches = FMSAPIMatchDetailsParser(2016, 'nyny').parse(json.loads(f.read()))

            self.assertTrue(isinstance(matches, dict))
            self.assertEqual(len(matches), 0)

    def test_parse_qual(self):
        with open('test_data/fms_api/2016_nyny_qual_breakdown.json', 'r') as f:
            matches = FMSAPIMatchDetailsParser(2016, 'nyny').parse(json.loads(f.read()))

            self.assertTrue(isinstance(matches, dict))
            self.assertEqual(len(matches), 88)

    def test_parse_playoff(self):
        with open('test_data/fms_api/2016_nyny_playoff_breakdown.json', 'r') as f:
            matches = FMSAPIMatchDetailsParser(2016, 'nyny').parse(json.loads(f.read()))

            self.assertTrue(isinstance(matches, dict))
            self.assertEqual(len(matches), 15)

    def test_parse_playoff_with_octofinals(self):
        with open('test_data/fms_api/2016_micmp_staging_playoff_breakdown.json', 'r') as f:
            matches = FMSAPIMatchDetailsParser(2016, 'micmp').parse(json.loads(f.read()))

            self.assertTrue(isinstance(matches, dict))
            self.assertEquals(len(matches), 36)
