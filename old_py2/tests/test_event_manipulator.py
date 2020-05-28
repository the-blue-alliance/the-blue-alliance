import datetime
import json
import unittest2

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from consts.event_type import EventType
from helpers.event_manipulator import EventManipulator
from models.event import Event


class TestEventManipulator(unittest2.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_taskqueue_stub(root_path=".")
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        self.maxDiff = None

        self.old_event = Event(
            id="2011ct",
            end_date=datetime.datetime(2011, 4, 2, 0, 0),
            event_short="ct",
            event_type_enum=EventType.REGIONAL,
            district_key=None,
            first_eid="5561",
            name="Northeast Utilities FIRST Connecticut Regional",
            start_date=datetime.datetime(2011, 3, 31, 0, 0),
            year=2011,
            venue_address="Connecticut Convention Center\r\n100 Columbus Blvd\r\nHartford, CT 06103\r\nUSA",
            website="http://www.ctfirst.org/ctr",
            webcast_json=json.dumps([{'type': 'twitch', 'channel': 'bar'}]),
        )

        self.new_event = Event(
            id="2011ct",
            end_date=datetime.datetime(2011, 4, 2, 0, 0),
            event_short="ct",
            event_type_enum=EventType.REGIONAL,
            district_key=None,
            first_eid="5561",
            name="Northeast Utilities FIRST Connecticut Regional",
            start_date=datetime.datetime(2011, 3, 31, 0, 0),
            year=2011,
            venue_address="Connecticut Convention Center\r\n100 Columbus Blvd\r\nHartford, CT 06103\r\nUSA",
            website="http://www.ctfirst.org/ctr",
            facebook_eid="7",
            webcast_json=json.dumps([{'type': 'ustream', 'channel': 'foo'}]),
        )

    def tearDown(self):
        self.testbed.deactivate()

    def assertMergedEvent(self, event):
        self.assertOldEvent(event)
        self.assertEqual(event.facebook_eid, "7")
        self.assertEqual(event.webcast[0]['type'], 'twitch')
        self.assertEqual(event.webcast[0]['channel'], 'bar')
        self.assertEqual(event.webcast[1]['type'], 'ustream')
        self.assertEqual(event.webcast[1]['channel'], 'foo')

    def assertOldEvent(self, event):
        self.assertEqual(event.key.id(), "2011ct")
        self.assertEqual(event.name, "Northeast Utilities FIRST Connecticut Regional")
        self.assertEqual(event.event_type_enum, EventType.REGIONAL)
        self.assertEqual(event.district_key, None)
        self.assertEqual(event.start_date, datetime.datetime(2011, 3, 31, 0, 0))
        self.assertEqual(event.end_date, datetime.datetime(2011, 4, 2, 0, 0))
        self.assertEqual(event.year, 2011)
        self.assertEqual(event.venue_address, "Connecticut Convention Center\r\n100 Columbus Blvd\r\nHartford, CT 06103\r\nUSA")
        self.assertEqual(event.website, "http://www.ctfirst.org/ctr")
        self.assertEqual(event.event_short, "ct")

    def test_createOrUpdate(self):
        EventManipulator.createOrUpdate(self.old_event)
        self.assertOldEvent(Event.get_by_id("2011ct"))
        EventManipulator.createOrUpdate(self.new_event)
        self.assertMergedEvent(Event.get_by_id("2011ct"))

    def test_findOrSpawn(self):
        self.old_event.put()
        self.assertMergedEvent(EventManipulator.findOrSpawn(self.new_event))

    def test_updateMerge(self):
        self.assertMergedEvent(EventManipulator.updateMerge(self.new_event, self.old_event))
