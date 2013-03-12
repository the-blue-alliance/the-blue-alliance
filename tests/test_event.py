import datetime
import unittest2
import json

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from helpers.event_manipulator import EventManipulator
from models.event import Event

class TestEventManipulator(unittest2.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()

        self.future_event = Event(
            id = "2011ct",
            end_date = datetime.datetime.today() + datetime.timedelta(days=5),
            event_short = "ct",
            event_type = "Regional",
            first_eid = "5561",
            name = "Northeast Utilities FIRST Connecticut Regional",
            start_date = datetime.datetime.today() + datetime.timedelta(days=1),
            year = 2011,
            venue_address = "Connecticut Convention Center\r\n100 Columbus Blvd\r\nHartford, CT 06103\r\nUSA",
            website = "http://www.ctfirst.org/ctr"
        )

        self.present_event = Event(
            id = "2011ct",
            end_date = datetime.datetime.today() + datetime.timedelta(days=1),
            event_short = "ct",
            event_type = "Regional",
            first_eid = "5561",
            name = "Northeast Utilities FIRST Connecticut Regional",
            start_date = datetime.datetime.today() - datetime.timedelta(days=2),
            year = 2011,
            venue_address = "Connecticut Convention Center\r\n100 Columbus Blvd\r\nHartford, CT 06103\r\nUSA",
            website = "http://www.ctfirst.org/ctr"
        )

        self.past_event = Event(
            id = "2011ct",
            end_date = datetime.datetime.today() - datetime.timedelta(days=1),
            event_short = "ct",
            event_type = "Regional",
            first_eid = "5561",
            name = "Northeast Utilities FIRST Connecticut Regional",
            start_date = datetime.datetime.today() - datetime.timedelta(days=5),
            year = 2011,
            venue_address = "Connecticut Convention Center\r\n100 Columbus Blvd\r\nHartford, CT 06103\r\nUSA",
            website = "http://www.ctfirst.org/ctr"
        )
        
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
