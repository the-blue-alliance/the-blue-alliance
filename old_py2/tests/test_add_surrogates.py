import unittest2

from appengine_fixture_loader.loader import load_fixture
from google.appengine.ext import testbed
from google.appengine.ext import ndb

from helpers.match_helper import MatchHelper
from models.event import Event
from models.match import Match


class TestAddSurrogates(unittest2.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_taskqueue_stub(root_path=".")
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        load_fixture('test_data/2016cama_no_surrogate.json',
                     kind={'Event': Event, 'Match': Match},
                     post_processor=self.eventKeyAdder)
        self.event = Event.get_by_id('2016cama')
        self.assertIsNotNone(self.event)

    def tearDown(self):
        self.testbed.deactivate()

    def eventKeyAdder(self, obj):
        obj.event = ndb.Key(Event, '2016cama')

    def test_event_winner(self):
        MatchHelper.add_surrogates(self.event)
        for match in self.event.matches:
            if match.comp_level != 'qm' or match.match_number != 18:
                for alliance_color in ['red', 'blue']:
                    self.assertEqual(match.alliances[alliance_color]['surrogates'], [])
            else:
                self.assertEqual(match.alliances['red']['surrogates'], ['frc5496'])
                self.assertEqual(match.alliances['blue']['surrogates'], ['frc1323'])
