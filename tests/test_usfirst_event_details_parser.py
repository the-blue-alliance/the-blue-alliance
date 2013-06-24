import unittest2
import datetime

from datafeeds.usfirst_event_details_parser import UsfirstEventDetailsParser
from models.event import Event

class TestUsfirstEventDetailsParser(unittest2.TestCase):
    def test_parse2012ct(self):
        with open('test_data/usfirst_html/usfirst_event_details_2012ct.html', 'r') as f: 
            event = UsfirstEventDetailsParser.parse(f.read())
        
        self.assertEqual(event["name"], "Northeast Utilities FIRST Connecticut Regional")
        self.assertEqual(event["event_type"], Event.REGIONAL)
        self.assertEqual(event["start_date"], datetime.datetime(2012, 3, 29, 0, 0))
        self.assertEqual(event["end_date"], datetime.datetime(2012, 3, 31, 0, 0))
        self.assertEqual(event["year"], 2012)
        self.assertEqual(event["venue_address"], "Connecticut Convention Center\r\n100 Columbus Blvd\r\nHartford, CT 06103\r\nUSA")
        self.assertEqual(event["website"], "http://www.ctfirst.org/ctr")
        self.assertEqual(event["event_short"], "ct")

    def test_parse2013flbr(self):
        with open('test_data/usfirst_html/usfirst_event_details_2013flbr.html', 'r') as f:
            event = UsfirstEventDetailsParser.parse(f.read())

        self.assertEqual(event["name"], "South Florida Regional")
        self.assertEqual(event["event_type"], Event.REGIONAL)
        self.assertEqual(event["start_date"], datetime.datetime(2013, 3, 28, 0, 0))
        self.assertEqual(event["end_date"], datetime.datetime(2013, 3, 30, 0, 0))
        self.assertEqual(event["year"], 2013)
        self.assertEqual(event["venue_address"], "Great Fort Lauderdale & Broward County Convention Center\r\n1950 Eisenhower Boulevard\r\nFort Lauderdale, FL 33316\r\nUSA")
        self.assertEqual(event["website"], "http://firstinflorida.org")
        self.assertEqual(event["event_short"], "flbr")