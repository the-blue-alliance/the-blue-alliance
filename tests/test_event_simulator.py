import json
import unittest2

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from helpers.event_simulator import EventSimulator
from helpers.match_helper import MatchHelper
from models.event import Event
from models.event_details import EventDetails
from models.match import Match


class TestEventSimulator(unittest2.TestCase):
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

    def test_event_smulator(self):
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
        self.assertEqual(len(event.matches), 72)
        for match in event.matches:
            self.assertEqual(match.comp_level, 'qm')
            self.assertFalse(match.has_been_played)
            self.assertEqual(match.score_breakdown, None)
            self.assertEqual(match.actual_time, None)

        # After each qual match
        for i in xrange(72):
            self.es.step()
            event = Event.get_by_id('2016nytr')
            self.assertNotEqual(event, None)
            # self.assertNotEqual(event.details, None)
            # self.assertEqual(event.details.alliance_selections, None)
            self.assertEqual(len(event.matches), 72)

            matches = MatchHelper.play_order_sort_matches(event.matches)
            for j, match in enumerate(matches):
                if j <= i:
                    self.assertTrue(match.has_been_played)
                else:
                    self.assertFalse(match.has_been_played)

        # After alliance selections
        self.es.step()
        event = Event.get_by_id('2016nytr')
        self.assertNotEqual(event, None)
        # self.assertNotEqual(event.details, None)
        # self.assertNotEqual(event.details.alliance_selections, None)
        self.assertEqual(len(event.matches), 72)

        # QF schedule added
        self.es.step()
        event = Event.get_by_id('2016nytr')
        self.assertNotEqual(event, None)
        self.assertEqual(event.details, None)
        self.assertEqual(len(event.matches), 84)
        for match in event.matches:
            if match.comp_level == 'qm':
                self.assertTrue(match.has_been_played)
            else:
                self.assertEqual(match.comp_level, 'qf')
                self.assertFalse(match.has_been_played)
                self.assertEqual(match.score_breakdown, None)
                self.assertEqual(match.actual_time, None)

        # After each QF match
        for i in xrange(72, 82):
            self.es.step()
            event = Event.get_by_id('2016nytr')
            self.assertNotEqual(event, None)
            # self.assertNotEqual(event.details, None)
            # self.assertEqual(event.details.alliance_selections, None)
            if i <= 76:
                self.assertEqual(len(event.matches), 84)
            elif i <= 78:
                self.assertEqual(len(event.matches), 83)
            else:
                self.assertEqual(len(event.matches), 82)

            matches = MatchHelper.play_order_sort_matches(event.matches)
            for j, match in enumerate(matches):
                if match.key.id() in {'2016nytr_qf1m3', '2016nytr_qf3m3'}:
                    # Unneeded tiebreak matches
                    self.assertFalse(match.has_been_played)
                elif j <= i:
                    self.assertTrue(match.has_been_played)
                else:
                    self.assertFalse(match.has_been_played)

        # SF schedule added
        self.es.step()
        event = Event.get_by_id('2016nytr')
        self.assertNotEqual(event, None)
        self.assertEqual(event.details, None)
        self.assertEqual(len(event.matches), 88)
        for match in event.matches:
            if match.comp_level in {'qm', 'qf'}:
                self.assertTrue(match.has_been_played)
            else:
                self.assertEqual(match.comp_level, 'sf')
                self.assertFalse(match.has_been_played)
                self.assertEqual(match.score_breakdown, None)
                self.assertEqual(match.actual_time, None)

        # After each SF match
        for i in xrange(82, 87):
            self.es.step()
            event = Event.get_by_id('2016nytr')
            self.assertNotEqual(event, None)
            # self.assertNotEqual(event.details, None)
            # self.assertEqual(event.details.alliance_selections, None)
            if i <= 84:
                self.assertEqual(len(event.matches), 88)
            else:
                self.assertEqual(len(event.matches), 87)

            matches = MatchHelper.play_order_sort_matches(event.matches)
            for j, match in enumerate(matches):
                if match.key.id() == '2016nytr_sf1m3':
                    # Unneeded tiebreak matches
                    self.assertFalse(match.has_been_played)
                elif j <= i:
                    self.assertTrue(match.has_been_played)
                else:
                    self.assertFalse(match.has_been_played)

        # F schedule added
        self.es.step()
        event = Event.get_by_id('2016nytr')
        self.assertNotEqual(event, None)
        self.assertEqual(event.details, None)
        self.assertEqual(len(event.matches), 90)
        for match in event.matches:
            if match.comp_level in {'qm', 'qf', 'sf'}:
                self.assertTrue(match.has_been_played)
            else:
                self.assertEqual(match.comp_level, 'f')
                self.assertFalse(match.has_been_played)
                self.assertEqual(match.score_breakdown, None)
                self.assertEqual(match.actual_time, None)

        # After each F match
        for i in xrange(87, 90):
            self.es.step()
            event = Event.get_by_id('2016nytr')
            self.assertNotEqual(event, None)
            # self.assertNotEqual(event.details, None)
            # self.assertEqual(event.details.alliance_selections, None)
            self.assertEqual(len(event.matches), 90)

            matches = MatchHelper.play_order_sort_matches(event.matches)
            for j, match in enumerate(matches):
                if j <= i:
                    self.assertTrue(match.has_been_played)
                else:
                    self.assertFalse(match.has_been_played)
