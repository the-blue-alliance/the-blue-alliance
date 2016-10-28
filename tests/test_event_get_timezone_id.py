import unittest2

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from datafeeds.usfirst_event_details_parser import UsfirstEventDetailsParser
from helpers.event_helper import EventHelper


class TestEventGetTimezoneId(unittest2.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_urlfetch_stub()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

    def test_2012ct_no_location(self):
        with open('test_data/usfirst_html/usfirst_event_details_2012ct.html', 'r') as f:
            event, _ = UsfirstEventDetailsParser.parse(f.read())
        event['location'] = None
        self.assertEqual(EventHelper.get_lat_lon(event['location'], '{}{}'.format(event['year'], event['event_short'])), None)
        self.assertEqual(EventHelper.get_timezone_id(event['location'], '{}{}'.format(event['year'], event['event_short'])), None)

    def test_2012ct_bad_location(self):
        with open('test_data/usfirst_html/usfirst_event_details_2012ct.html', 'r') as f:
            event, _ = UsfirstEventDetailsParser.parse(f.read())
        event['location'] = "somewhere on mars"
        self.assertEqual(EventHelper.get_lat_lon(event['location'], '{}{}'.format(event['year'], event['event_short'])), None)
        self.assertEqual(EventHelper.get_timezone_id(event['location'], '{}{}'.format(event['year'], event['event_short'])), None)

    def test_2012ct(self):
        with open('test_data/usfirst_html/usfirst_event_details_2012ct.html', 'r') as f:
            event, _ = UsfirstEventDetailsParser.parse(f.read())

        self.assertEqual(EventHelper.get_lat_lon(event['location'], '{}{}'.format(event['year'], event['event_short'])), (41.76371109999999, -72.6850932))
        self.assertEqual(EventHelper.get_timezone_id(event['location'], '{}{}'.format(event['year'], event['event_short'])), 'America/New_York')

    def test_2013flbr(self):
        with open('test_data/usfirst_html/usfirst_event_details_2013flbr.html', 'r') as f:
            event, _ = UsfirstEventDetailsParser.parse(f.read())

        self.assertEqual(EventHelper.get_lat_lon(event['location'], '{}{}'.format(event['year'], event['event_short'])), (26.1224386, -80.13731740000001))
        self.assertEqual(EventHelper.get_timezone_id(event['location'], '{}{}'.format(event['year'], event['event_short'])), 'America/New_York')

    def test_2013casj(self):
        with open('test_data/usfirst_html/usfirst_event_details_2013casj.html', 'r') as f:
            event, _ = UsfirstEventDetailsParser.parse(f.read())

        self.assertEqual(EventHelper.get_lat_lon(event['location'], '{}{}'.format(event['year'], event['event_short'])), (37.3382082, -121.8863286))
        self.assertEqual(EventHelper.get_timezone_id(event['location'], '{}{}'.format(event['year'], event['event_short'])), 'America/Los_Angeles')

    def test_2001sj(self):
        with open('test_data/usfirst_html/usfirst_event_details_2001ca2.html', 'r') as f:
            event, _ = UsfirstEventDetailsParser.parse(f.read())

        self.assertEqual(EventHelper.get_lat_lon(event['location'], '{}{}'.format(event['year'], event['event_short'])), (37.3382082, -121.8863286))
        self.assertEqual(EventHelper.get_timezone_id(event['location'], '{}{}'.format(event['year'], event['event_short'])), 'America/Los_Angeles')

    def test_2005is(self):
        with open('test_data/usfirst_html/usfirst_event_details_2005is.html', 'r') as f:
            event, _ = UsfirstEventDetailsParser.parse(f.read())

        self.assertEqual(EventHelper.get_lat_lon(event['location'], '{}{}'.format(event['year'], event['event_short'])), (32.7940463, 34.989571))
        self.assertEqual(EventHelper.get_timezone_id(event['location'], '{}{}'.format(event['year'], event['event_short'])), 'Asia/Jerusalem')

    def test_2005or(self):
        with open('test_data/usfirst_html/usfirst_event_details_2005or.html', 'r') as f:
            event, _ = UsfirstEventDetailsParser.parse(f.read())

        self.assertEqual(EventHelper.get_lat_lon(event['location'], '{}{}'.format(event['year'], event['event_short'])), (45.5230622, -122.6764816))
        self.assertEqual(EventHelper.get_timezone_id(event['location'], '{}{}'.format(event['year'], event['event_short'])), 'America/Los_Angeles')

    def test_1997il(self):
        with open('test_data/usfirst_html/usfirst_event_details_1997il.html', 'r') as f:
            event, _ = UsfirstEventDetailsParser.parse(f.read())

        self.assertEqual(EventHelper.get_lat_lon(event['location'], '{}{}'.format(event['year'], event['event_short'])), (41.8781136, -87.6297982))
        self.assertEqual(EventHelper.get_timezone_id(event['location'], '{}{}'.format(event['year'], event['event_short'])), 'America/Chicago')

    def test_2002sj(self):
        with open('test_data/usfirst_html/usfirst_event_details_2002sj.html', 'r') as f:
            event, _ = UsfirstEventDetailsParser.parse(f.read())

        self.assertEqual(EventHelper.get_lat_lon(event['location'], '{}{}'.format(event['year'], event['event_short'])), (37.3382082, -121.8863286))
        self.assertEqual(EventHelper.get_timezone_id(event['location'], '{}{}'.format(event['year'], event['event_short'])), 'America/Los_Angeles')
