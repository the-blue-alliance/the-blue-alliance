import json
import unittest2

from datafeeds.parsers.fms_api.fms_api_district_list_parser import FMSAPIDistrictListParser

from google.appengine.ext import ndb
from google.appengine.ext import testbed


class TestFMSAPIDistrictListParser(unittest2.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

    def tearDown(self):
        self.testbed.deactivate()

    def test_parse_district_list(self):
        with open('test_data/fms_api/2018_districts.json') as f:
            districts = FMSAPIDistrictListParser(2018).parse(json.loads(f.read()))

            self.assertTrue(isinstance(districts, list))
            self.assertEquals(len(districts), 10)

            new_england = districts[7]
            self.assertEquals(new_england.key_name, '2018ne')
            self.assertEquals(new_england.abbreviation, 'ne')
            self.assertEquals(new_england.year, 2018)
            self.assertEquals(new_england.display_name, 'New England')
