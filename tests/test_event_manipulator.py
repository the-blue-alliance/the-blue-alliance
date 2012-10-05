import datetime
import unittest2
import json

from google.appengine.ext import db
from google.appengine.ext import testbed

from helpers.event_manipulator import EventManipulator
from models.event import Event

class TestEventManipulator(unittest2.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()

        self.old_event = Event(
            key_name = "2011ct",
            end_date = datetime.datetime(2011, 4, 2, 0, 0),
            event_short = "ct",
            event_type = "Regional",
            first_eid = "5561",
            name = "Northeast Utilities FIRST Connecticut Regional",
            start_date = datetime.datetime(2011, 3, 31, 0, 0),
            year = 2011,
            venue_address = "Connecticut Convention Center\r\n100 Columbus Blvd\r\nHartford, CT 06103\r\nUSA",
            website = "http://www.ctfirst.org/ctr"
        )

        self.new_event = Event(
            key_name = "2011ct",
            end_date = datetime.datetime(2011, 4, 2, 0, 0),
            event_short = "ct",
            event_type = "Regional",
            first_eid = "5561",
            name = "Northeast Utilities FIRST Connecticut Regional",
            start_date = datetime.datetime(2011, 3, 31, 0, 0),
            year = 2011,
            venue_address = "Connecticut Convention Center\r\n100 Columbus Blvd\r\nHartford, CT 06103\r\nUSA",
            website = "http://www.ctfirst.org/ctr",

            oprs = [1.0, 2.0, 3.0],
            opr_teams = [177, 195, 233], # are these really stored as ints or strings? -gregmarra 20120922
            facebook_eid = "7",
            webcast_json = json.dumps({'type': 'ustream', 'channel': 'foo'})
        )
        
    def tearDown(self):
        self.testbed.deactivate()

    def assertMergedEvent(self, event):
        self.assertOldEvent(event)
        self.assertEqual(event.oprs, [1, 2, 3])
        self.assertEqual(event.opr_teams, [177, 195, 233])
        self.assertEqual(event.facebook_eid, "7")
        self.assertEqual(event.webcast['type'], 'ustream')
        self.assertEqual(event.webcast['channel'], 'foo')

    def assertOldEvent(self, event):
        self.assertEqual(event.key().name(), "2011ct")
        self.assertEqual(event.name, "Northeast Utilities FIRST Connecticut Regional")
        self.assertEqual(event.event_type, "Regional")
        self.assertEqual(event.start_date, datetime.datetime(2011, 3, 31, 0, 0))
        self.assertEqual(event.end_date, datetime.datetime(2011, 4, 2, 0, 0))
        self.assertEqual(event.year, 2011)
        self.assertEqual(event.venue_address, "Connecticut Convention Center\r\n100 Columbus Blvd\r\nHartford, CT 06103\r\nUSA")
        self.assertEqual(event.website, "http://www.ctfirst.org/ctr")
        self.assertEqual(event.event_short, "ct")

    def test_createOrUpdate(self):
        EventManipulator.createOrUpdate(self.old_event)
        self.assertOldEvent(Event.get_by_key_name("2011ct"))
        EventManipulator.createOrUpdate(self.new_event)
        self.assertMergedEvent(Event.get_by_key_name("2011ct"))

    def test_findOrSpawn(self):
        db.put(self.old_event)
        self.assertMergedEvent(EventManipulator.findOrSpawn(self.new_event))

    def test_updateMerge(self):
        self.assertMergedEvent(EventManipulator.updateMerge(self.new_event, self.old_event))
