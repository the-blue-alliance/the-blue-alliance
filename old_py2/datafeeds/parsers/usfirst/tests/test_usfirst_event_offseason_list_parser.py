import unittest2
import datetime

from consts.event_type import EventType
from datafeeds.usfirst_event_offseason_list_parser import UsfirstEventOffseasonListParser


@unittest2.skip
class TestUsfirstEventOffseasonListParser(unittest2.TestCase):
    def test_parse_2013(self):
        with open('test_data/usfirst_html/usfirst_event_offseason_list_2016.html', 'r') as f:
            events, _ = UsfirstEventOffseasonListParser.parse(f.read())

        self.assertEqual(len(events), 6)

        self.assertEqual(events[0]["first_eid"], "6481")
        self.assertEqual(events[0]["event_type_enum"], EventType.OFFSEASON)
        self.assertEqual(events[0]["name"], "Missouri Robotics State Championship")
        self.assertEqual(events[0]["start_date"], datetime.datetime(2016, 5, 14))
        self.assertEqual(events[0]["end_date"], datetime.datetime(2016, 5, 14))
        self.assertEqual(events[0]["state_prov"], "MO")

        self.assertEqual(events[1]["first_eid"], "10526")
        self.assertEqual(events[1]["event_type_enum"], EventType.OFFSEASON)
        self.assertEqual(events[1]["name"], "Hudson Valley Rally")
        self.assertEqual(events[1]["start_date"], datetime.datetime(2016, 6, 4))
        self.assertEqual(events[1]["end_date"], datetime.datetime(2016, 6, 4))
        self.assertEqual(events[1]["state_prov"], "NY")

        self.assertEqual(events[4]["start_date"], datetime.datetime(2016, 9, 23))
        self.assertEqual(events[4]["end_date"], datetime.datetime(2016, 9, 24))
