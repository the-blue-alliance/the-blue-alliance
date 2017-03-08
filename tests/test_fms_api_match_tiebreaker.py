import datetime
import unittest2

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from datafeeds.datafeed_fms_api import DatafeedFMSAPI
from helpers.match_manipulator import MatchManipulator
from models.event import Event
from models.match import Match


class TestFMSAPIMatchTiebreaker(unittest2.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_app_identity_stub()
        self.testbed.init_blobstore_stub()
        self.testbed.init_urlfetch_stub()
        self.testbed.init_taskqueue_stub(root_path=".")
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        Event(
            id='2017flwp',
            event_short='flwp',
            year=2017,
            event_type_enum=0,
            timezone_id='America/New_York'
        ).put()

    def tearDown(self):
        self.testbed.deactivate()

    def test(self):
        MatchManipulator.createOrUpdate(DatafeedFMSAPI('v2.0', sim_time=datetime.datetime(2017, 3, 04, 21, 22)).getMatches('2017flwp'))
        sf_matches = Match.query(Match.event==ndb.Key(Event, '2017flwp'), Match.comp_level=='sf').fetch()
        self.assertEqual(len(sf_matches), 5)
        old_match = Match.get_by_id('2017flwp_sf1m3')
        self.assertNotEqual(old_match, None)
        self.assertEqual(old_match.alliances['red']['score'], 255)
        self.assertEqual(old_match.alliances['blue']['score'], 255)

        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        MatchManipulator.createOrUpdate(DatafeedFMSAPI('v2.0', sim_time=datetime.datetime(2017, 3, 04, 21, 35)).getMatches('2017flwp'))
        sf_matches = Match.query(Match.event==ndb.Key(Event, '2017flwp'), Match.comp_level=='sf').fetch()
        self.assertEqual(len(sf_matches), 6)
        new_match = Match.get_by_id('2017flwp_sf1m3')
        self.assertNotEqual(new_match, None)

        self.assertEqual(old_match, new_match)

        tiebreaker_match = Match.get_by_id('2017flwp_sf1m4')
        self.assertNotEqual(tiebreaker_match, None)

        self.assertEqual(tiebreaker_match.alliances['red']['score'], 165)
        self.assertEqual(tiebreaker_match.alliances['blue']['score'], 263)
