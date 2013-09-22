import unittest2
import datetime

from consts.event_type import EventType
from datafeeds.usfirst_event_offseason_list_parser import UsfirstEventOffseasonListParser


class TestUsfirstEventOffseasonListParser(unittest2.TestCase):
    def test_parse_2013(self):
        with open('test_data/usfirst_html/usfirst_event_offseason_list_2013.html', 'r') as f:
            events, _ = UsfirstEventOffseasonListParser.parse(f.read())

        self.assertEqual(len(events), 35)

        self.assertEqual(events[0]["url_slug"], "off-season-ozark-mountain-2013")
        self.assertEqual(events[0]["event_type_enum"], EventType.OFFSEASON)
        self.assertEqual(events[0]["name"], "Ozark Mountain")
        self.assertEqual(events[0]["start_date"], datetime.datetime(2013, 9, 13))
        self.assertEqual(events[0]["end_date"], datetime.datetime(2013, 9, 14))

        self.assertEqual(events[1]["url_slug"], "off-season-powerhouse-pwnage")
        self.assertEqual(events[1]["event_type_enum"], EventType.OFFSEASON)
        self.assertEqual(events[1]["name"], "Powerhouse Pwnage")
        self.assertEqual(events[0]["start_date"], datetime.datetime(2013, 9, 13))
        self.assertEqual(events[0]["end_date"], datetime.datetime(2013, 9, 14))
