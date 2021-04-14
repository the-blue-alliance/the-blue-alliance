import unittest2
import datetime

from consts.event_type import EventType
from datafeeds.usfirst_event_details_parser import UsfirstEventDetailsParser


@unittest2.skip
class TestUsfirstEventDetailsParser(unittest2.TestCase):
    def test_parse2012ct(self):
        with open('test_data/usfirst_html/usfirst_event_details_2012ct.html', 'r') as f:
            event, _ = UsfirstEventDetailsParser.parse(f.read())

        self.assertEqual(event["name"], "Northeast Utilities FIRST Connecticut Regional")
        self.assertEqual(event["short_name"], "Northeast Utilities FIRST Connecticut")
        self.assertEqual(event["event_type_enum"], EventType.REGIONAL)
        self.assertEqual(event["start_date"], datetime.datetime(2012, 3, 29, 0, 0))
        self.assertEqual(event["end_date"], datetime.datetime(2012, 3, 31, 0, 0))
        self.assertEqual(event["year"], 2012)
        self.assertEqual(event["venue_address"], "Connecticut Convention Center\r\n100 Columbus Blvd\r\nHartford, CT 06103\r\nUSA")
        self.assertEqual(event["venue"], "Connecticut Convention Center")
        self.assertEqual(event["location"], "Hartford, CT, USA")
        self.assertEqual(event["website"], "http://www.ctfirst.org/ctr")
        self.assertEqual(event["event_short"], "ct")

    def test_parse2013flbr(self):
        with open('test_data/usfirst_html/usfirst_event_details_2013flbr.html', 'r') as f:
            event, _ = UsfirstEventDetailsParser.parse(f.read())

        self.assertEqual(event["name"], "South Florida Regional")
        self.assertEqual(event["short_name"], "South Florida")
        self.assertEqual(event["event_type_enum"], EventType.REGIONAL)
        self.assertEqual(event["start_date"], datetime.datetime(2013, 3, 28, 0, 0))
        self.assertEqual(event["end_date"], datetime.datetime(2013, 3, 30, 0, 0))
        self.assertEqual(event["year"], 2013)
        self.assertEqual(event["venue_address"], "Great Fort Lauderdale & Broward County Convention Center\r\n1950 Eisenhower Boulevard\r\nFort Lauderdale, FL 33316\r\nUSA")
        self.assertEqual(event["venue"], "Great Fort Lauderdale & Broward County Convention Center")
        self.assertEqual(event["location"], "Fort Lauderdale, FL, USA")
        self.assertEqual(event["website"], "http://firstinflorida.org")
        self.assertEqual(event["event_short"], "flbr")

    def test_parse2013casj(self):
        with open('test_data/usfirst_html/usfirst_event_details_2013casj.html', 'r') as f:
            event, _ = UsfirstEventDetailsParser.parse(f.read())

        self.assertEqual(event["name"], "Silicon Valley Regional")
        self.assertEqual(event["short_name"], "Silicon Valley")
        self.assertEqual(event["event_type_enum"], EventType.REGIONAL)
        self.assertEqual(event["start_date"], datetime.datetime(2013, 4, 4, 0, 0))
        self.assertEqual(event["end_date"], datetime.datetime(2013, 4, 6, 0, 0))
        self.assertEqual(event["year"], 2013)
        self.assertEqual(event["venue_address"], "San Jose State University\r\nThe Event Center\r\nSan Jose, CA 95192\r\nUSA")
        self.assertEqual(event["venue"], "San Jose State University")
        self.assertEqual(event["location"], "San Jose, CA, USA")
        self.assertEqual(event["website"], "http://www.firstsv.org")
        self.assertEqual(event["event_short"], "casj")

    def test_parse2001sj(self):
        with open('test_data/usfirst_html/usfirst_event_details_2001ca2.html', 'r') as f:
            event, _ = UsfirstEventDetailsParser.parse(f.read())

        self.assertEqual(event["name"], "Silicon Valley Regional")
        self.assertEqual(event["short_name"], "Silicon Valley")
        self.assertEqual(event["event_type_enum"], EventType.REGIONAL)
        self.assertEqual(event["start_date"], datetime.datetime(2001, 3, 22, 0, 0))
        self.assertEqual(event["end_date"], datetime.datetime(2001, 3, 24, 0, 0))
        self.assertEqual(event["year"], 2001)
        self.assertEqual(event["venue_address"], "San Jose, CA\r\nUSA")
        self.assertEqual(event["location"], "San Jose, CA, USA")
        self.assertEqual(event["event_short"], "ca2")

    def test_parse2005is(self):
        with open('test_data/usfirst_html/usfirst_event_details_2005is.html', 'r') as f:
            event, _ = UsfirstEventDetailsParser.parse(f.read())

        self.assertEqual(event["name"], "GM/Technion University Israel Pilot Regional")
        self.assertEqual(event["short_name"], "GM/Technion University Israel Pilot")
        self.assertEqual(event["event_type_enum"], EventType.REGIONAL)
        self.assertEqual(event["start_date"], datetime.datetime(2005, 3, 9, 0, 0))
        self.assertEqual(event["end_date"], datetime.datetime(2005, 3, 9, 0, 0))
        self.assertEqual(event["year"], 2005)
        self.assertEqual(event["venue_address"], "Haifa Sports Coliseum\r\nHaifa, Haifa\r\nIsrael")
        self.assertEqual(event["venue"], "Haifa Sports Coliseum")
        self.assertEqual(event["location"], "Haifa, Haifa, Israel")
        self.assertEqual(event["event_short"], "is")

    def test_parse2005or(self):
        with open('test_data/usfirst_html/usfirst_event_details_2005or.html', 'r') as f:
            event, _ = UsfirstEventDetailsParser.parse(f.read())

        self.assertEqual(event["name"], "Pacific Northwest Regional")
        self.assertEqual(event["short_name"], "Pacific Northwest")
        self.assertEqual(event["event_type_enum"], EventType.REGIONAL)
        self.assertEqual(event["start_date"], datetime.datetime(2005, 3, 10, 0, 0))
        self.assertEqual(event["end_date"], datetime.datetime(2005, 3, 12, 0, 0))
        self.assertEqual(event["year"], 2005)
        self.assertEqual(event["venue_address"], "Memorial Coliseum\r\nPortland, OR 97201\r\nUSA")
        self.assertEqual(event["venue"], "Memorial Coliseum")
        self.assertEqual(event["location"], "Portland, OR, USA")
        self.assertEqual(event["event_short"], "or")

    def test_parse_1997il(self):
        with open('test_data/usfirst_html/usfirst_event_details_1997il.html', 'r') as f:
            event, _ = UsfirstEventDetailsParser.parse(f.read())

        self.assertEqual(event["name"], "Motorola Midwest Regional")
        self.assertEqual(event["short_name"], "Motorola Midwest")
        self.assertEqual(event["event_type_enum"], EventType.REGIONAL)
        self.assertEqual(event["start_date"], datetime.datetime(1997, 3, 6, 0, 0))
        self.assertEqual(event["end_date"], datetime.datetime(1997, 3, 8, 0, 0))
        self.assertEqual(event["year"], 1997)
        self.assertEqual(event["venue_address"], "William Rainey Harper College\r\nChicago, IL\r\nUSA")
        self.assertEqual(event["venue"], "William Rainey Harper College")
        self.assertEqual(event["location"], "Chicago, IL, USA")
        self.assertEqual(event["event_short"], "il")

    def test_parse_2002sj(self):
        with open('test_data/usfirst_html/usfirst_event_details_2002sj.html', 'r') as f:
            event, _ = UsfirstEventDetailsParser.parse(f.read())

        self.assertEqual(event["name"], "Silicon Valley Regional")
        self.assertEqual(event["short_name"], "Silicon Valley")
        self.assertEqual(event["event_type_enum"], EventType.REGIONAL)
        self.assertEqual(event["start_date"], datetime.datetime(2002, 3, 28, 0, 0))
        self.assertEqual(event["end_date"], datetime.datetime(2002, 3, 30, 0, 0))
        self.assertEqual(event["year"], 2002)
        self.assertEqual(event["venue_address"], "San Jose, CA\r\nUSA")
        self.assertEqual(event["location"], "San Jose, CA, USA")
        self.assertEqual(event["event_short"], "sj")
