import datetime
import json
import unittest2

from datafeeds.parsers.fms_api.fms_api_event_list_parser import FMSAPIEventListParser

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from consts.district_type import DistrictType
from consts.event_type import EventType
from models.sitevar import Sitevar


class TestFMSAPIEventListParser(unittest2.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

    def tearDown(self):
        self.testbed.deactivate()

    def test_parse_event_list(self):
        with open('test_data/fms_api/2015_event_list.json', 'r') as f:
            events, districts = FMSAPIEventListParser(2015).parse(json.loads(f.read()))

            self.assertTrue(isinstance(events, list))
            self.assertTrue(isinstance(districts, list))

            # File has 5 events, but we ignore CMP divisions (only subdivisions), so only 4 are expected back
            self.assertEquals(len(events), 4)
            self.assertEquals(len(districts), 1)

    def test_parse_regional_event(self):
        with open('test_data/fms_api/2015_event_list.json', 'r') as f:
            events, districts = FMSAPIEventListParser(2015).parse(json.loads(f.read()))
            event = events[0]

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
            self.assertEquals(event.country, "USA")
            self.assertEquals(event.year, 2015)
            self.assertEquals(event.event_type_enum, EventType.REGIONAL)
            self.assertEquals(event.district_key, None)

    def test_parse_district_event(self):
        with open('test_data/fms_api/2015_event_list.json', 'r') as f:
            events, districts = FMSAPIEventListParser(2015).parse(json.loads(f.read()))
            event = events[1]
            district = districts[0]

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
            self.assertEquals(event.country, "USA")
            self.assertEquals(event.year, 2015)
            self.assertEquals(event.event_type_enum, EventType.DISTRICT)
            self.assertEquals(event.district_key, district.key)

            self.assertEquals(district.key_name, "2015ne")
            self.assertEquals(district.abbreviation, "ne")
            self.assertEquals(district.year, 2015)

    def test_parse_district_cmp(self):
        with open('test_data/fms_api/2015_event_list.json', 'r') as f:
            events, districts = FMSAPIEventListParser(2015).parse(json.loads(f.read()))
            event = events[2]

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
            self.assertEquals(event.country, "USA")
            self.assertEquals(event.year, 2015)
            self.assertEquals(event.event_type_enum, EventType.DISTRICT_CMP)
            self.assertEquals(event.district_key, districts[0].key)

    def test_parse_cmp_subdivision(self):
        with open('test_data/fms_api/2015_event_list.json', 'r') as f:
            events, districts = FMSAPIEventListParser(2015).parse(json.loads(f.read()))
            event = events[3]

            self.assertEquals(event.key_name, "2015tes")
            self.assertEquals(event.name, "Tesla Division")
            self.assertEquals(event.short_name, "Tesla")
            self.assertEquals(event.event_short, "tes")
            self.assertEquals(event.official, True)
            self.assertEquals(event.start_date, datetime.datetime(year=2015, month=4, day=22, hour=0, minute=0, second=0))
            self.assertEquals(event.end_date, datetime.datetime(year=2015, month=4, day=25, hour=23, minute=59, second=59))
            self.assertEquals(event.venue, "Edward Jones Dome")
            self.assertEquals(event.city, "St. Louis")
            self.assertEquals(event.state_prov, "MO")
            self.assertEquals(event.country, "USA")
            self.assertEquals(event.year, 2015)
            self.assertEquals(event.event_type_enum, EventType.CMP_DIVISION)
            self.assertEquals(event.district_key, None)

    def test_parse_2017_event(self):
        with open('test_data/fms_api/2017_event_list.json', 'r') as f:
            events, districts = FMSAPIEventListParser(2017).parse(json.loads(f.read()))
            self.assertEqual(len(events), 164)
            self.assertEqual(len(districts), 10)
            event = events[16]

            self.assertEquals(event.key_name, "2017casj")
            self.assertEquals(event.name, "Silicon Valley Regional")
            self.assertEquals(event.short_name, "Silicon Valley")
            self.assertEquals(event.event_short, "casj")
            self.assertEquals(event.official, True)
            self.assertEquals(event.start_date, datetime.datetime(year=2017, month=3, day=29, hour=0, minute=0, second=0))
            self.assertEquals(event.end_date, datetime.datetime(year=2017, month=4, day=1, hour=23, minute=59, second=59))
            self.assertEquals(event.venue, "San Jose State University - The Event Center")
            self.assertEquals(event.city, "San Jose")
            self.assertEquals(event.state_prov, "CA")
            self.assertEquals(event.country, "USA")
            self.assertEquals(event.year, 2017)
            self.assertEquals(event.event_type_enum, EventType.REGIONAL)
            self.assertEquals(event.district_key, None)

            # New in 2017
            self.assertEquals(event.website, "http://www.firstsv.org")

    def test_parse_2017_events_with_cmp_hacks(self):
        hack_sitevar = Sitevar(id='cmp_registration_hacks')
        hack_sitevar.contents = {
            "event_name_override": [
                {"event": "2017cmpmo", "name": "FIRST Championship Event", "short_name": "Championship"},
                {"event": "2017cmptx", "name": "FIRST Championship Event", "short_name": "Championship"}],
            "set_start_to_last_day": ["2017cmptx", "2017cmpmo"],
            "divisions_to_skip": ["2017arc", "2017cars", "2017cur", "2017dal", "2017dar"],
        }
        hack_sitevar.put()

        with open('test_data/fms_api/2017_event_list.json', 'r') as f:
            events, districts = FMSAPIEventListParser(2017).parse(json.loads(f.read()))
            self.assertEqual(len(events), 159)
            self.assertEqual(len(districts), 10)

            non_einstein_types = EventType.CMP_EVENT_TYPES
            non_einstein_types.remove(EventType.CMP_FINALS)
            for key in hack_sitevar.contents['divisions_to_skip']:
                self.assertFalse(filter(lambda e: e.key_name == key, events))

            einstein_stl = next(e for e in events if e.key_name == '2017cmpmo')
            self.assertIsNotNone(einstein_stl)
            self.assertEqual(einstein_stl.name, "FIRST Championship Event (St. Louis)")
            self.assertEqual(einstein_stl.short_name, "Championship (St. Louis)")
            self.assertEquals(einstein_stl.start_date, datetime.datetime(year=2017, month=4, day=29, hour=0, minute=0, second=0))
            self.assertEquals(einstein_stl.end_date, datetime.datetime(year=2017, month=4, day=29, hour=23, minute=59, second=59))

            einstein_hou = next(e for e in events if e.key_name == '2017cmptx')
            self.assertIsNotNone(einstein_hou)
            self.assertEqual(einstein_hou.name, "FIRST Championship Event (Houston)")
            self.assertEqual(einstein_hou.short_name, "Championship (Houston)")
            self.assertEquals(einstein_hou.start_date, datetime.datetime(year=2017, month=4, day=22, hour=0, minute=0, second=0))
            self.assertEquals(einstein_hou.end_date, datetime.datetime(year=2017, month=4, day=22, hour=23, minute=59, second=59))
