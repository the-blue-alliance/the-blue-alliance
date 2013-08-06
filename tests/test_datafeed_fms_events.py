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
        self.assertTrue(self.find2012CT(events) or self.find2013CT(events))

    def find2012CT(self, events):
        found_ct = False
        for event in events:
            if event.event_short == "ct":
                found_ct = True
                self.assertEqual(event.key.id(), "2012ct")
                self.assertEqual(event.end_date, datetime.datetime(2012, 03, 31))
                self.assertEqual(event.event_short, "ct")
                self.assertEqual(event.first_eid, "7627")
                #self.assertEqual(event.location, "Hartford, CT")
                self.assertEqual(event.name, "Northeast Utilities FIRST Connecticut Regional")
                self.assertEqual(event.official, True)
                self.assertEqual(event.start_date, datetime.datetime(2012, 03, 29))
                self.assertEqual(event.venue, "Connecticut Convention Center")
                self.assertEqual(event.year, 2012)

        return found_ct

    def find2013CT(self, events):
        found_ct = False
        for event in events:
            if event.event_short == "ctha":
                found_ct = True
                self.assertEqual(event.key.id(), "2013ctha")
                self.assertEqual(event.end_date, datetime.datetime(2013, 03, 30))
                self.assertEqual(event.event_short, "ctha")
                self.assertEqual(event.first_eid, "8985")
                #self.assertEqual(event.location, "Hartford, CT")
                self.assertEqual(event.name, "Connecticut Regional sponsored by UTC")
                self.assertEqual(event.official, True)
                self.assertEqual(event.start_date, datetime.datetime(2013, 03, 28))
                self.assertEqual(event.venue, "Connecticut Convention Center")
                self.assertEqual(event.year, 2013)

        return found_ct
