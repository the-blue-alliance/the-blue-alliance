import datetime
import unittest2
import json

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from helpers.event.event_test_creator import EventTestCreator

class TestEventManipulator(unittest2.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()

        self.future_event = EventTestCreator.createFutureEvent()
        self.present_event = EventTestCreator.createPresentEvent()
        self.past_event = EventTestCreator.createPastEvent()
        
    def tearDown(self):
        self.testbed.deactivate()

    def test_datesFuture(self):
        self.assertFalse(self.future_event.now)
        self.assertTrue(self.future_event.within_a_day)
        self.assertFalse(self.future_event.withinDays(0,3))
        self.assertTrue(self.future_event.withinDays(-3,0))

    def test_datesPast(self):
        self.assertFalse(self.past_event.now)
        self.assertTrue(self.past_event.within_a_day)
        self.assertTrue(self.past_event.withinDays(0,3))
        self.assertFalse(self.past_event.withinDays(-3,0))

    def test_datesPresent(self):
        self.assertTrue(self.present_event.now)
        self.assertTrue(self.present_event.withinDays(-1,1))
