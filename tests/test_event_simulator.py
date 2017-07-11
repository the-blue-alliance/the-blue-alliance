import unittest2

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from helpers.event_simulator import EventSimulator
from helpers.match_helper import MatchHelper
from models.event import Event


class TestEventSimulator(unittest2.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        self.testbed.init_taskqueue_stub(root_path=".")

        self._alliance_selections = [{u'declines': [], u'backup': None, u'name': u'Alliance 1', u'picks': [u'frc359', u'frc3990', u'frc4508']}, {u'declines': [], u'backup': None, u'name': u'Alliance 2', u'picks': [u'frc5254', u'frc20', u'frc229']}, {u'declines': [], u'backup': None, u'name': u'Alliance 3', u'picks': [u'frc5236', u'frc2791', u'frc3624']}, {u'declines': [], u'backup': None, u'name': u'Alliance 4', u'picks': [u'frc3419', u'frc5240', u'frc663']}, {u'declines': [], u'backup': None, u'name': u'Alliance 5', u'picks': [u'frc48', u'frc1493', u'frc1551']}, {u'declines': [], u'backup': None, u'name': u'Alliance 6', u'picks': [u'frc250', u'frc333', u'frc145']}, {u'declines': [], u'backup': None, u'name': u'Alliance 7', u'picks': [u'frc358', u'frc3003', u'frc527']}, {u'declines': [], u'backup': None, u'name': u'Alliance 8', u'picks': [u'frc4930', u'frc3044', u'frc4481']}]
        self._alliance_selections_with_backup = [{u'declines': [], u'backup': None, u'name': u'Alliance 1', u'picks': [u'frc359', u'frc3990', u'frc4508']}, {u'declines': [], u'backup': {u'in': u'frc1665', u'out': u'frc229'}, u'name': u'Alliance 2', u'picks': [u'frc5254', u'frc20', u'frc229']}, {u'declines': [], u'backup': None, u'name': u'Alliance 3', u'picks': [u'frc5236', u'frc2791', u'frc3624']}, {u'declines': [], u'backup': None, u'name': u'Alliance 4', u'picks': [u'frc3419', u'frc5240', u'frc663']}, {u'declines': [], u'backup': None, u'name': u'Alliance 5', u'picks': [u'frc48', u'frc1493', u'frc1551']}, {u'declines': [], u'backup': None, u'name': u'Alliance 6', u'picks': [u'frc250', u'frc333', u'frc145']}, {u'declines': [], u'backup': None, u'name': u'Alliance 7', u'picks': [u'frc358', u'frc3003', u'frc527']}, {u'declines': [], u'backup': None, u'name': u'Alliance 8', u'picks': [u'frc4930', u'frc3044', u'frc4481']}]

    def tearDown(self):
        self.testbed.deactivate()

    def test_event_smulator(self):
        es = EventSimulator()

        # Before anything has happened
        event = Event.get_by_id('2016nytr')
        self.assertNotEqual(event, None)
        self.assertEqual(event.details, None)
        self.assertEqual(event.matches, [])

        # Qual match schedule added
        es.step()
        event = Event.get_by_id('2016nytr')
        self.assertNotEqual(event, None)
        self.assertNotEqual(event.details, None)
        for rank in event.details.rankings2:
            self.assertEqual(rank['sort_orders'][0], 0)

        self.assertEqual(len(event.matches), 72)
        for match in event.matches:
            self.assertEqual(match.comp_level, 'qm')
            self.assertFalse(match.has_been_played)
            self.assertEqual(match.actual_time, None)

        # After each qual match
        for i in xrange(72):
            es.step()
            event = Event.get_by_id('2016nytr')
            self.assertNotEqual(event, None)
            self.assertEqual(event.details.alliance_selections, None)
            self.assertEqual(len(event.matches), 72)

            matches = MatchHelper.play_order_sort_matches(event.matches)
            for j, match in enumerate(matches):
                if j <= i:
                    self.assertTrue(match.has_been_played)
                    self.assertNotEqual(match.actual_time, None)
                else:
                    self.assertFalse(match.has_been_played)

        # Check some final rankings
        self.assertEqual(event.details.rankings2[0]['sort_orders'][0], 22)
        self.assertEqual(event.details.rankings2[-1]['sort_orders'][0], 4)

        # After alliance selections
        es.step()
        event = Event.get_by_id('2016nytr')
        self.assertNotEqual(event, None)
        self.assertEqual(event.details.alliance_selections, self._alliance_selections)
        self.assertEqual(len(event.matches), 72)

        # QF schedule added
        es.step()
        event = Event.get_by_id('2016nytr')
        self.assertNotEqual(event, None)
        self.assertEqual(event.details.alliance_selections, self._alliance_selections)
        self.assertEqual(len(event.matches), 84)
        for match in event.matches:
            if match.comp_level == 'qm':
                self.assertTrue(match.has_been_played)
                self.assertNotEqual(match.actual_time, None)
            else:
                self.assertEqual(match.comp_level, 'qf')
                self.assertFalse(match.has_been_played)
                self.assertEqual(match.actual_time, None)

        # After each QF match
        for i in xrange(72, 82):
            es.step()
            event = Event.get_by_id('2016nytr')
            self.assertNotEqual(event, None)
            self.assertEqual(event.details.alliance_selections, self._alliance_selections)

            if i <= 75:
                self.assertEqual(len(event.matches), 84)
            elif i <= 77:
                self.assertEqual(len(event.matches), 86)  # 1 match removed, 3 added
            else:
                self.assertEqual(len(event.matches), 88)  # 1 match removed, 3 added

            matches = MatchHelper.play_order_sort_matches(event.matches)
            for j, match in enumerate(matches):
                if match.key.id() in {'2016nytr_qf1m3', '2016nytr_qf3m3'}:
                    # Unneeded tiebreak matches
                    self.assertFalse(match.has_been_played)
                elif j <= i:
                    self.assertTrue(match.has_been_played)
                    self.assertNotEqual(match.actual_time, None)
                else:
                    self.assertFalse(match.has_been_played)

        # Check SF Matches
        event = Event.get_by_id('2016nytr')
        self.assertNotEqual(event, None)
        self.assertEqual(event.details.alliance_selections, self._alliance_selections)
        self.assertEqual(len(event.matches), 88)
        for match in event.matches:
            if match.comp_level in {'qm', 'qf'}:
                self.assertTrue(match.has_been_played)
                self.assertNotEqual(match.actual_time, None)
            else:
                self.assertEqual(match.comp_level, 'sf')
                self.assertFalse(match.has_been_played)
                self.assertEqual(match.actual_time, None)

        # After each SF match
        for i in xrange(82, 87):
            es.step()
            event = Event.get_by_id('2016nytr')
            self.assertNotEqual(event, None)

            if i < 85:
                self.assertEqual(event.details.alliance_selections, self._alliance_selections)
            else:
                self.assertEqual(event.details.alliance_selections, self._alliance_selections_with_backup)

            if i <= 83:
                self.assertEqual(len(event.matches), 88)
            else:
                self.assertEqual(len(event.matches), 90)  # 1 match removed, 3 added

            matches = MatchHelper.play_order_sort_matches(event.matches)
            for j, match in enumerate(matches):
                if match.key.id() == '2016nytr_sf1m3':
                    # Unneeded tiebreak matches
                    self.assertFalse(match.has_been_played)
                elif j <= i:
                    self.assertTrue(match.has_been_played)
                    self.assertNotEqual(match.actual_time, None)
                else:
                    self.assertFalse(match.has_been_played)

        # Check F Matches
        event = Event.get_by_id('2016nytr')
        self.assertNotEqual(event, None)
        self.assertEqual(event.details.alliance_selections, self._alliance_selections_with_backup)
        self.assertEqual(len(event.matches), 90)
        for match in event.matches:
            if match.comp_level in {'qm', 'qf', 'sf'}:
                self.assertTrue(match.has_been_played)
                self.assertNotEqual(match.actual_time, None)
            else:
                self.assertEqual(match.comp_level, 'f')
                self.assertFalse(match.has_been_played)
                self.assertEqual(match.actual_time, None)

        # After each F match
        for i in xrange(87, 90):
            es.step()
            event = Event.get_by_id('2016nytr')
            self.assertNotEqual(event, None)
            self.assertEqual(event.details.alliance_selections, self._alliance_selections_with_backup)
            self.assertEqual(len(event.matches), 90)

            matches = MatchHelper.play_order_sort_matches(event.matches)
            for j, match in enumerate(matches):
                if j <= i:
                    self.assertTrue(match.has_been_played)
                    self.assertNotEqual(match.actual_time, None)
                else:
                    self.assertFalse(match.has_been_played)

    def test_event_smulator_batch_advance(self):
        es = EventSimulator(batch_advance=True)

        # Before anything has happened
        event = Event.get_by_id('2016nytr')
        self.assertNotEqual(event, None)
        self.assertEqual(event.details, None)
        self.assertEqual(event.matches, [])

        # Qual match schedule added
        es.step()
        event = Event.get_by_id('2016nytr')
        self.assertNotEqual(event, None)
        self.assertNotEqual(event.details, None)
        for rank in event.details.rankings2:
            self.assertEqual(rank['sort_orders'][0], 0)

        self.assertEqual(len(event.matches), 72)
        for match in event.matches:
            self.assertEqual(match.comp_level, 'qm')
            self.assertFalse(match.has_been_played)
            self.assertEqual(match.actual_time, None)

        # After each qual match
        for i in xrange(72):
            es.step()
            event = Event.get_by_id('2016nytr')
            self.assertNotEqual(event, None)
            self.assertEqual(event.details.alliance_selections, None)
            self.assertEqual(len(event.matches), 72)

            matches = MatchHelper.play_order_sort_matches(event.matches)
            for j, match in enumerate(matches):
                if j <= i:
                    self.assertTrue(match.has_been_played)
                    self.assertNotEqual(match.actual_time, None)
                else:
                    self.assertFalse(match.has_been_played)

        # Check some final rankings
        self.assertEqual(event.details.rankings2[0]['sort_orders'][0], 22)
        self.assertEqual(event.details.rankings2[-1]['sort_orders'][0], 4)

        # After alliance selections
        es.step()
        event = Event.get_by_id('2016nytr')
        self.assertNotEqual(event, None)
        self.assertEqual(event.details.alliance_selections, self._alliance_selections)
        self.assertEqual(len(event.matches), 72)

        # QF schedule added
        es.step()
        event = Event.get_by_id('2016nytr')
        self.assertNotEqual(event, None)
        self.assertEqual(event.details.alliance_selections, self._alliance_selections)
        self.assertEqual(len(event.matches), 84)
        for match in event.matches:
            if match.comp_level == 'qm':
                self.assertTrue(match.has_been_played)
                self.assertNotEqual(match.actual_time, None)
            else:
                self.assertEqual(match.comp_level, 'qf')
                self.assertFalse(match.has_been_played)
                self.assertEqual(match.actual_time, None)

        # After each QF match
        for i in xrange(72, 82):
            es.step()
            event = Event.get_by_id('2016nytr')
            self.assertNotEqual(event, None)
            self.assertEqual(event.details.alliance_selections, self._alliance_selections)
            if i <= 75:
                self.assertEqual(len(event.matches), 84)
            elif i <= 77:
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
                    self.assertNotEqual(match.actual_time, None)
                else:
                    self.assertFalse(match.has_been_played)

        # SF schedule added
        es.step()
        event = Event.get_by_id('2016nytr')
        self.assertNotEqual(event, None)
        self.assertEqual(event.details.alliance_selections, self._alliance_selections)
        self.assertEqual(len(event.matches), 88)
        for match in event.matches:
            if match.comp_level in {'qm', 'qf'}:
                self.assertTrue(match.has_been_played)
                self.assertNotEqual(match.actual_time, None)
            else:
                self.assertEqual(match.comp_level, 'sf')
                self.assertFalse(match.has_been_played)
                self.assertEqual(match.actual_time, None)

        # After each SF match
        for i in xrange(82, 87):
            es.step()
            event = Event.get_by_id('2016nytr')
            self.assertNotEqual(event, None)

            if i < 85:
                self.assertEqual(event.details.alliance_selections, self._alliance_selections)
            else:
                self.assertEqual(event.details.alliance_selections, self._alliance_selections_with_backup)

            if i <= 83:
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
                    self.assertNotEqual(match.actual_time, None)
                else:
                    self.assertFalse(match.has_been_played)

        # F schedule added
        es.step()
        event = Event.get_by_id('2016nytr')
        self.assertNotEqual(event, None)
        self.assertEqual(event.details.alliance_selections, self._alliance_selections_with_backup)
        self.assertEqual(len(event.matches), 90)
        for match in event.matches:
            if match.comp_level in {'qm', 'qf', 'sf'}:
                self.assertTrue(match.has_been_played)
                self.assertNotEqual(match.actual_time, None)
            else:
                self.assertEqual(match.comp_level, 'f')
                self.assertFalse(match.has_been_played)
                self.assertEqual(match.actual_time, None)

        # After each F match
        for i in xrange(87, 90):
            es.step()
            event = Event.get_by_id('2016nytr')
            self.assertNotEqual(event, None)
            self.assertEqual(event.details.alliance_selections, self._alliance_selections_with_backup)
            self.assertEqual(len(event.matches), 90)

            matches = MatchHelper.play_order_sort_matches(event.matches)
            for j, match in enumerate(matches):
                if j <= i:
                    self.assertTrue(match.has_been_played)
                    self.assertNotEqual(match.actual_time, None)
                else:
                    self.assertFalse(match.has_been_played)
