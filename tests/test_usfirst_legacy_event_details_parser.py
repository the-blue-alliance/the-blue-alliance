import unittest2
import datetime

from consts.event_type import EventType
from datafeeds.usfirst_legacy_event_details_parser import UsfirstLegacyEventDetailsParser


@unittest2.skip
class TestUsfirstLegacyEventDetailsParser(unittest2.TestCase):
    def test_parse2012ct(self):
        with open('test_data/usfirst_legacy_html/usfirst_event_details_2012ct.html', 'r') as f:
            event, _ = UsfirstLegacyEventDetailsParser.parse(f.read())

        self.assertEqual(event["name"], "Northeast Utilities FIRST Connecticut Regional")
        self.assertEqual(event["short_name"], "Northeast Utilities FIRST Connecticut")
        self.assertEqual(event["event_type_enum"], EventType.REGIONAL)
        self.assertEqual(event["start_date"], datetime.datetime(2012, 3, 29, 0, 0))
        self.assertEqual(event["end_date"], datetime.datetime(2012, 3, 31, 0, 0))
        self.assertEqual(event["year"], 2012)
        self.assertEqual(event["venue_address"], "Connecticut Convention Center\r\n100 Columbus Blvd\r\nHartford, CT 06103\r\nUSA")
        self.assertEqual(event["location"], "Hartford, CT, USA")
        self.assertEqual(event["website"], "http://www.ctfirst.org/ctr")
        self.assertEqual(event["event_short"], "ct")

    def test_parse2013flbr(self):
        with open('test_data/usfirst_legacy_html/usfirst_event_details_2013flbr.html', 'r') as f:
            event, _ = UsfirstLegacyEventDetailsParser.parse(f.read())

        self.assertEqual(event["name"], "South Florida Regional")
        self.assertEqual(event["short_name"], "South Florida")
        self.assertEqual(event["event_type_enum"], EventType.REGIONAL)
        self.assertEqual(event["start_date"], datetime.datetime(2013, 3, 28, 0, 0))
        self.assertEqual(event["end_date"], datetime.datetime(2013, 3, 30, 0, 0))
        self.assertEqual(event["year"], 2013)
        self.assertEqual(event["venue_address"], "Great Fort Lauderdale & Broward County Convention Center\r\n1950 Eisenhower Boulevard\r\nFort Lauderdale, FL 33316\r\nUSA")
        self.assertEqual(event["location"], "Fort Lauderdale, FL, USA")
        self.assertEqual(event["website"], "http://firstinflorida.org")
        self.assertEqual(event["event_short"], "flbr")

    def test_parse2014casj(self):
        with open('test_data/usfirst_legacy_html/usfirst_event_details_2014casj.html', 'r') as f:
            event, _ = UsfirstLegacyEventDetailsParser.parse(f.read())

        self.assertEqual(event["name"], "Silicon Valley Regional")
        self.assertEqual(event["short_name"], "Silicon Valley")
        self.assertEqual(event["event_type_enum"], EventType.REGIONAL)
        self.assertEqual(event["start_date"], datetime.datetime(2014, 4, 3, 0, 0))
        self.assertEqual(event["end_date"], datetime.datetime(2014, 4, 5, 0, 0))
        self.assertEqual(event["year"], 2014)
        self.assertEqual(event["venue_address"], "San Jose State University\r\nThe Event Center\r\nOne Washington Square\r\nSan Jose, CA 95112\r\nUSA")
        self.assertEqual(event["location"], "San Jose, CA, USA")
        self.assertEqual(event["website"], "http://www.firstsv.org")
        self.assertEqual(event["event_short"], "casj")

    def test_parse2014lake(self):
        with open('test_data/usfirst_legacy_html/usfirst_event_details_2014lake.html', 'r') as f:
            event, _ = UsfirstLegacyEventDetailsParser.parse(f.read())

        self.assertEqual(event["name"], "Bayou Regional")
        self.assertEqual(event["short_name"], "Bayou")
        self.assertEqual(event["event_type_enum"], EventType.REGIONAL)
        self.assertEqual(event["start_date"], datetime.datetime(2014, 4, 3, 0, 0))
        self.assertEqual(event["end_date"], datetime.datetime(2014, 4, 5, 0, 0))
        self.assertEqual(event["year"], 2014)
        self.assertEqual(event["website"], "http://www.frcbayouregional.com")
        self.assertEqual(event["event_short"], "lake")

    def test_parse2014nvlv_preliminary(self):
        with open('test_data/usfirst_legacy_html/usfirst_event_details_2014nvlv_preliminary.html', 'r') as f:
            event, _ = UsfirstLegacyEventDetailsParser.parse(f.read())

        self.assertEqual(event["name"], "Las Vegas Regional - Preliminary")
        self.assertEqual(event["short_name"], "Las Vegas")
        self.assertEqual(event["event_type_enum"], EventType.REGIONAL)
        self.assertEqual(event["start_date"], datetime.datetime(2014, 12, 31, 0, 0))
        self.assertEqual(event["end_date"], datetime.datetime(2014, 12, 31, 0, 0))
        self.assertEqual(event["year"], 2014)
        self.assertEqual(event["website"], "http://www.firstnv.org")
        self.assertEqual(event["event_short"], "nvlv")
