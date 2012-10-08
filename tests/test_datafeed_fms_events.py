import unittest2
import datetime

from google.appengine.ext import testbed

from datafeeds.datafeed_fms import DatafeedFms

class TestDatafeedFmsEvents(unittest2.TestCase):
    
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_urlfetch_stub()
        
        self.datafeed = DatafeedFms()
    
    def tearDown(self):
        self.testbed.deactivate()
    
    def test_getFmsEventList(self):
        events = self.datafeed.getFmsEventList()
        self.findCT(events)
    
    def findCT(self, events):
        found_ct = False
        for event in events:
            if event.event_short == "ct":
                found_ct = True
                self.assertEqual(event.key.id(), "2012ct")
                self.assertEqual(event.end_date, datetime.datetime(2012, 03, 31))
                self.assertEqual(event.event_short, "ct")
                self.assertEqual(event.first_eid, "7627")
                self.assertEqual(event.location, "Hartford, CT")
                self.assertEqual(event.name, "Northeast Utilities FIRST Connecticut Regional")
                self.assertEqual(event.official, True)
                self.assertEqual(event.start_date, datetime.datetime(2012, 03, 29))
                self.assertEqual(event.venue, "Connecticut Convention Center")
                self.assertEqual(event.year, 2012)
        
        self.assertTrue(found_ct)
        self.assertTrue(len(events) > 0)
