import unittest2

from datafeeds.fms_event_list_parser import FmsEventListParser

class TestFmsEventListParser(unittest2.TestCase):
    def test_parse(self):
        with open('test_data/usfirst_html/fms_event_list_2012.html', 'r') as f:
            events = FmsEventListParser.parse(f.read())

        self.assertEqual(len(events), 74)

        self.assertEqual(events[0]["first_eid"], "7689")
        self.assertEqual(events[0]["name"], "Alamo Regional")

        self.assertEqual(events[1]["first_eid"], "7585")
        self.assertEqual(events[1]["name"], "BAE Systems Granite State Regional")
