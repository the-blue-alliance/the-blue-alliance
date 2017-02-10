import json
import unittest2

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from helpers.event_simulator import EventSimulator
from models.event import Event
from models.event_details import EventDetails
from models.match import Match


class TestAwardManipulator(unittest2.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        self.testbed.init_taskqueue_stub(root_path=".")

        self.es = EventSimulator()

    def tearDown(self):
        self.testbed.deactivate()

    def test_stuff(self):
        # Before anything has happened
        event = Event.get_by_id('2016nytr')
        self.assertNotEqual(event, None)
        self.assertEqual(event.details, None)
        self.assertEqual(event.matches, [])

        # Qual match schedule added
        self.es.step()
        event = Event.get_by_id('2016nytr')
        self.assertNotEqual(event, None)
        self.assertEqual(event.details, None)
        self.assertNotEqual(event.matches, [])
        for match in event.matches:
            self.assertEqual(match.comp_level, 'qm')
            self.assertFalse(match.has_been_played)
            self.assertEqual(match.score_breakdown, None)
            self.assertEqual(match.actual_time, None)
