import unittest2
import datetime

from datafeeds.usfirst_event_list_parser import UsfirstEventListParser
from models.event import Event

class TestUsfirstEventListParser(unittest2.TestCase):
    def test_parse(self):
        with open('test_data/usfirst_html/usfirst_event_list_2012.html', 'r') as f: 
            events = UsfirstEventListParser.parse(f.read())

        self.assertEqual(len(events), 69)
        
        self.assertEqual(events[0]["first_eid"], "7617")
        self.assertEqual(events[0]["event_type"], Event.REGIONAL)
        self.assertEqual(events[0]["name"], "Greater Kansas City Regional")
        
        self.assertEqual(events[1]["first_eid"], "7585")
        self.assertEqual(events[1]["event_type"], Event.REGIONAL)
        self.assertEqual(events[1]["name"], "BAE Systems Granite State Regional")

        self.assertEqual(events[51]["event_type"], Event.REGIONAL)
        self.assertEqual(events[52]["event_type"], Event.DISTRICT_CMP)
        self.assertEqual(events[54]["event_type"], Event.DISTRICT)
