import unittest2

from consts.district_type import DistrictType
from consts.event_type import EventType
from datafeeds.usfirst_event_list_parser import UsfirstEventListParser


@unittest2.skip
class TestUsfirstEventListParser(unittest2.TestCase):
    def test_parse_2012(self):
        with open('test_data/usfirst_html/usfirst_event_list_2012.html', 'r') as f:
            events, _ = UsfirstEventListParser.parse(f.read())

        self.assertEqual(len(events), 69)

        self.assertEqual(events[0]["first_eid"], "7617")
        self.assertEqual(events[0]["event_type_enum"], EventType.REGIONAL)
        self.assertEqual(events[0]["name"], "Greater Kansas City Regional")

        self.assertEqual(events[1]["first_eid"], "7585")
        self.assertEqual(events[1]["event_type_enum"], EventType.REGIONAL)
        self.assertEqual(events[1]["name"], "BAE Systems Granite State Regional")

        self.assertEqual(events[51]["event_type_enum"], EventType.REGIONAL)
        self.assertEqual(events[52]["event_type_enum"], EventType.DISTRICT_CMP)
        self.assertEqual(events[54]["event_type_enum"], EventType.DISTRICT)

    def test_parse_2014(self):
        with open('test_data/usfirst_html/usfirst_event_list_2014.html', 'r') as f:
            events, _ = UsfirstEventListParser.parse(f.read())

        self.assertEqual(len(events), 98)

        self.assertEqual(events[2]["first_eid"], "10851")
        self.assertEqual(events[2]["event_type_enum"], EventType.REGIONAL)
        self.assertEqual(events[2]["name"], "Alamo Regional sponsored by Rackspace Hosting")
        # self.assertEqual(events[2]["event_district_enum"], DistrictType.NO_DISTRICT)

        self.assertEqual(events[5]["first_eid"], "10807")
        self.assertEqual(events[5]["event_type_enum"], EventType.REGIONAL)
        self.assertEqual(events[5]["name"], "Israel Regional")
        # self.assertEqual(events[5]["event_district_enum"], DistrictType.NO_DISTRICT)

        self.assertEqual(events[56]["event_type_enum"], EventType.DISTRICT_CMP)
        # self.assertEqual(events[56]["event_district_enum"], DistrictType.NEW_ENGLAND)
        self.assertEqual(events[93]["event_type_enum"], EventType.DISTRICT)
        # self.assertEqual(events[93]["event_district_enum"], DistrictType.PACIFIC_NORTHWEST)
