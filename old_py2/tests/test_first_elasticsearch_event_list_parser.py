import datetime
import json
import unittest2

from datafeeds.parsers.first_elasticsearch.first_elasticsearch_event_list_parser import FIRSTElasticSearchEventListParser

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from consts.event_type import EventType
from models.district import District


class TestFIRSTElasticSearchEventListParser(unittest2.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        self.ne_district = District(
            id='2015ne',
            abbreviation='ne',
            year=2015,
            elasticsearch_name='NE FIRST'
        )
        self.ne_district.put()

    def tearDown(self):
        self.testbed.deactivate()

    def test_parse_event_list(self):
        with open('test_data/first_elasticsearch/2015_event_list.json', 'r') as f:
            events = FIRSTElasticSearchEventListParser(2015).parse(json.loads(f.read()))

            self.assertTrue(isinstance(events, list))

            self.assertEquals(len(events), 56 + 48 + 5)  # 56 regionals, 48 districts, 5 district championships

    def test_parse_regional_event(self):
        with open('test_data/first_elasticsearch/2015_event_list.json', 'r') as f:
            events = FIRSTElasticSearchEventListParser(2015).parse(json.loads(f.read()))

            for event in events:
                if event.key_name == '2015nyny':
                    self.assertEquals(event.key_name, "2015nyny")
                    self.assertEquals(event.name, "New York City Regional")
                    self.assertEquals(event.short_name, "New York City")
                    self.assertEquals(event.event_short, "nyny")
                    self.assertEquals(event.official, True)
                    self.assertEquals(event.start_date, datetime.datetime(year=2015, month=3, day=12, hour=0, minute=0, second=0))
                    self.assertEquals(event.end_date, datetime.datetime(year=2015, month=3, day=15, hour=23, minute=59, second=59))
                    self.assertEquals(event.venue, "Jacob K. Javits Convention Center")
                    self.assertEquals(event.city, "New York")
                    self.assertEquals(event.state_prov, "NY")
                    self.assertEquals(event.postalcode, "10001")
                    self.assertEquals(event.country, "USA")
                    self.assertEquals(event.venue_address, "Jacob K. Javits Convention Center\n655 West 34th Street\nNew York, NY 10001\nUSA")
                    self.assertEquals(event.year, 2015)
                    self.assertEquals(event.event_type_enum, EventType.REGIONAL)
                    self.assertEquals(event.district_key, None)
                    self.assertEquals(event.first_eid, '13339')
                    self.assertEquals(event.website, 'http://www.nycfirst.org')

    def test_parse_district_event(self):
        with open('test_data/first_elasticsearch/2015_event_list.json', 'r') as f:
            events = FIRSTElasticSearchEventListParser(2015).parse(json.loads(f.read()))
            for event in events:
                if event.key_name == '2015cthar':
                    self.assertEquals(event.key_name, "2015cthar")
                    self.assertEquals(event.name, "NE District - Hartford Event")
                    self.assertEquals(event.short_name, "Hartford")
                    self.assertEquals(event.event_short, "cthar")
                    self.assertEquals(event.official, True)
                    self.assertEquals(event.start_date, datetime.datetime(year=2015, month=3, day=27, hour=0, minute=0, second=0))
                    self.assertEquals(event.end_date, datetime.datetime(year=2015, month=3, day=29, hour=23, minute=59, second=59))
                    self.assertEquals(event.venue, "Hartford Public High School")
                    self.assertEquals(event.city, "Hartford")
                    self.assertEquals(event.state_prov, "CT")
                    self.assertEquals(event.postalcode, "06105")
                    self.assertEquals(event.country, "USA")
                    self.assertEquals(event.venue_address, "Hartford Public High School\n55 Forest Street\nHartford, CT 06105\nUSA")
                    self.assertEquals(event.year, 2015)
                    self.assertEquals(event.event_type_enum, EventType.DISTRICT)
                    self.assertEquals(event.district_key.id(), '2015ne')
                    self.assertEqual(event.district_key, self.ne_district.key)
                    self.assertEquals(event.first_eid, '13443')
                    self.assertEquals(event.website, 'http://www.nefirst.org/')

    def test_parse_district_cmp(self):
        with open('test_data/first_elasticsearch/2015_event_list.json', 'r') as f:
            events = FIRSTElasticSearchEventListParser(2015).parse(json.loads(f.read()))
            for event in events:
                if event.key_name == '2015necmp':
                    self.assertEquals(event.key_name, "2015necmp")
                    self.assertEquals(event.name, "NE FIRST District Championship presented by United Technologies")
                    self.assertEquals(event.short_name, "NE FIRST")
                    self.assertEquals(event.event_short, "necmp")
                    self.assertEquals(event.official, True)
                    self.assertEquals(event.start_date, datetime.datetime(year=2015, month=4, day=8, hour=0, minute=0, second=0))
                    self.assertEquals(event.end_date, datetime.datetime(year=2015, month=4, day=11, hour=23, minute=59, second=59))
                    self.assertEquals(event.venue, "Sports and Recreation Center, WPI")
                    self.assertEquals(event.city, "Worcester")
                    self.assertEquals(event.state_prov, "MA")
                    self.assertEquals(event.postalcode, "01609")
                    self.assertEquals(event.country, "USA")
                    self.assertEquals(event.venue_address, "Sports and Recreation Center, WPI\n100 Institute Road\nWorcester, MA 01609\nUSA")
                    self.assertEquals(event.year, 2015)
                    self.assertEquals(event.event_type_enum, EventType.DISTRICT_CMP)
                    self.assertEquals(event.district_key.id(), '2015ne')
                    self.assertEqual(event.district_key, self.ne_district.key)
                    self.assertEquals(event.first_eid, '13423')
                    self.assertEquals(event.website, 'http:///www.nefirst.org/')
