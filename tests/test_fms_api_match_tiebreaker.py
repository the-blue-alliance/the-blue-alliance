import datetime
import unittest2
import json

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from datafeeds.datafeed_fms_api import DatafeedFMSAPI
from helpers.match_helper import MatchHelper
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

    def tearDown(self):
        self.testbed.deactivate()

    def test_2017flwp_sequence(self):
        event = Event(
            id='2017flwp',
            event_short='flwp',
            year=2017,
            event_type_enum=0,
            timezone_id='America/New_York'
        )
        event.put()

        event_code = 'flwp'

        file_prefix = 'frc-api-response/v2.0/2017/schedule/{}/playoff/hybrid/'.format(event_code)
        context = ndb.get_context()
        result = context.urlfetch('https://www.googleapis.com/storage/v1/b/bucket/o?bucket=tbatv-prod-hrd.appspot.com&prefix={}'.format(file_prefix)).get_result()

        for item in json.loads(result.content)['items']:
            filename = item['name']
            time_str = filename.replace(file_prefix, '').replace('.json', '').strip()
            file_time = datetime.datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S.%f")
            query_time = file_time + datetime.timedelta(seconds=30)
            MatchManipulator.createOrUpdate(DatafeedFMSAPI('v2.0', sim_time=query_time).getMatches('2017{}'.format(event_code)), run_post_update_hook=False)
        MatchHelper.deleteInvalidMatches(event.matches, event)

        sf_matches = Match.query(Match.event == ndb.Key(Event, '2017flwp'), Match.comp_level == 'sf').fetch()
        self.assertEqual(len(sf_matches), 7)

        self.assertEqual(Match.get_by_id('2017flwp_sf1m1').alliances['red']['score'], 305)
        self.assertEqual(Match.get_by_id('2017flwp_sf1m1').alliances['blue']['score'], 255)
        self.assertEqual(Match.get_by_id('2017flwp_sf1m1').score_breakdown['red']['totalPoints'], 305)
        self.assertEqual(Match.get_by_id('2017flwp_sf1m1').score_breakdown['blue']['totalPoints'], 255)

        self.assertEqual(Match.get_by_id('2017flwp_sf1m2').alliances['red']['score'], 165)
        self.assertEqual(Match.get_by_id('2017flwp_sf1m2').alliances['blue']['score'], 258)
        self.assertEqual(Match.get_by_id('2017flwp_sf1m2').score_breakdown['red']['totalPoints'], 165)
        self.assertEqual(Match.get_by_id('2017flwp_sf1m2').score_breakdown['blue']['totalPoints'], 258)

        self.assertEqual(Match.get_by_id('2017flwp_sf1m3').alliances['red']['score'], 255)
        self.assertEqual(Match.get_by_id('2017flwp_sf1m3').alliances['blue']['score'], 255)
        self.assertEqual(Match.get_by_id('2017flwp_sf1m3').score_breakdown['red']['totalPoints'], 255)
        self.assertEqual(Match.get_by_id('2017flwp_sf1m3').score_breakdown['blue']['totalPoints'], 255)

        self.assertEqual(Match.get_by_id('2017flwp_sf1m4').alliances['red']['score'], 255)
        self.assertEqual(Match.get_by_id('2017flwp_sf1m4').alliances['blue']['score'], 255)
        self.assertEqual(Match.get_by_id('2017flwp_sf1m4').score_breakdown['red']['totalPoints'], 255)
        self.assertEqual(Match.get_by_id('2017flwp_sf1m4').score_breakdown['blue']['totalPoints'], 255)

        self.assertEqual(Match.get_by_id('2017flwp_sf1m5').alliances['red']['score'], 165)
        self.assertEqual(Match.get_by_id('2017flwp_sf1m5').alliances['blue']['score'], 263)
        self.assertEqual(Match.get_by_id('2017flwp_sf1m5').score_breakdown['red']['totalPoints'], 165)
        self.assertEqual(Match.get_by_id('2017flwp_sf1m5').score_breakdown['blue']['totalPoints'], 263)

    def test_2017flwp(self):
        event = Event(
            id='2017flwp',
            event_short='flwp',
            year=2017,
            event_type_enum=0,
            timezone_id='America/New_York'
        )
        event.put()

        MatchManipulator.createOrUpdate(DatafeedFMSAPI('v2.0', sim_time=datetime.datetime(2017, 3, 04, 21, 22)).getMatches('2017flwp'))
        MatchHelper.deleteInvalidMatches(event.matches, event)

        sf_matches = Match.query(Match.event == ndb.Key(Event, '2017flwp'), Match.comp_level == 'sf').fetch()
        self.assertEqual(len(sf_matches), 5)
        old_match = Match.get_by_id('2017flwp_sf1m3')
        self.assertNotEqual(old_match, None)
        self.assertEqual(old_match.alliances['red']['score'], 255)
        self.assertEqual(old_match.alliances['blue']['score'], 255)
        self.assertEqual(old_match.score_breakdown['red']['totalPoints'], 255)
        self.assertEqual(old_match.score_breakdown['blue']['totalPoints'], 255)

        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        MatchManipulator.createOrUpdate(DatafeedFMSAPI('v2.0', sim_time=datetime.datetime(2017, 3, 04, 21, 35)).getMatches('2017flwp'))
        MatchHelper.deleteInvalidMatches(event.matches, event)

        sf_matches = Match.query(Match.event == ndb.Key(Event, '2017flwp'), Match.comp_level == 'sf').fetch()
        self.assertEqual(len(sf_matches), 6)
        new_match = Match.get_by_id('2017flwp_sf1m3')
        self.assertNotEqual(new_match, None)

        self.assertEqual(old_match.alliances, new_match.alliances)
        self.assertEqual(old_match.score_breakdown, new_match.score_breakdown)

        tiebreaker_match = Match.get_by_id('2017flwp_sf1m4')
        self.assertNotEqual(tiebreaker_match, None)

        self.assertEqual(tiebreaker_match.alliances['red']['score'], 165)
        self.assertEqual(tiebreaker_match.alliances['blue']['score'], 263)
        self.assertEqual(tiebreaker_match.score_breakdown['red']['totalPoints'], 165)
        self.assertEqual(tiebreaker_match.score_breakdown['blue']['totalPoints'], 263)

    def test_2017pahat(self):
        event = Event(
            id='2017pahat',
            event_short='pahat',
            year=2017,
            event_type_enum=0,
            timezone_id='America/New_York'
        )
        event.put()

        MatchManipulator.createOrUpdate(DatafeedFMSAPI('v2.0', sim_time=datetime.datetime(2017, 3, 05, 20, 45)).getMatches('2017pahat'))
        MatchHelper.deleteInvalidMatches(event.matches, event)
        f_matches = Match.query(Match.event == ndb.Key(Event, '2017pahat'), Match.comp_level == 'f').fetch()
        self.assertEqual(len(f_matches), 3)
        old_match = Match.get_by_id('2017pahat_f1m2')
        self.assertNotEqual(old_match, None)
        self.assertEqual(old_match.alliances['red']['score'], 255)
        self.assertEqual(old_match.alliances['blue']['score'], 255)
        self.assertEqual(old_match.score_breakdown['red']['totalPoints'], 255)
        self.assertEqual(old_match.score_breakdown['blue']['totalPoints'], 255)

        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        MatchManipulator.createOrUpdate(DatafeedFMSAPI('v2.0', sim_time=datetime.datetime(2017, 3, 05, 21, 02)).getMatches('2017pahat'))
        MatchHelper.deleteInvalidMatches(event.matches, event)
        f_matches = Match.query(Match.event == ndb.Key(Event, '2017pahat'), Match.comp_level == 'f').fetch()
        self.assertEqual(len(f_matches), 4)
        new_match = Match.get_by_id('2017pahat_f1m2')
        self.assertNotEqual(new_match, None)

        self.assertEqual(old_match.alliances, new_match.alliances)
        self.assertEqual(old_match.score_breakdown, new_match.score_breakdown)

        tiebreaker_match = Match.get_by_id('2017pahat_f1m4')
        self.assertNotEqual(tiebreaker_match, None)

        self.assertEqual(tiebreaker_match.alliances['red']['score'], 240)
        self.assertEqual(tiebreaker_match.alliances['blue']['score'], 235)
        self.assertEqual(tiebreaker_match.score_breakdown['red']['totalPoints'], 240)
        self.assertEqual(tiebreaker_match.score_breakdown['blue']['totalPoints'], 235)

    def test_2017scmb_sequence(self):
        event = Event(
            id='2017scmb',
            event_short='scmb',
            year=2017,
            event_type_enum=0,
            timezone_id='America/New_York'
        )
        event.put()

        event_code = 'scmb'

        file_prefix = 'frc-api-response/v2.0/2017/schedule/{}/playoff/hybrid/'.format(event_code)
        context = ndb.get_context()
        result = context.urlfetch('https://www.googleapis.com/storage/v1/b/bucket/o?bucket=tbatv-prod-hrd.appspot.com&prefix={}'.format(file_prefix)).get_result()

        for item in json.loads(result.content)['items']:
            filename = item['name']
            time_str = filename.replace(file_prefix, '').replace('.json', '').strip()
            file_time = datetime.datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S.%f")
            query_time = file_time + datetime.timedelta(seconds=30)
            MatchManipulator.createOrUpdate(DatafeedFMSAPI('v2.0', sim_time=query_time).getMatches('2017{}'.format(event_code)), run_post_update_hook=False)
        MatchHelper.deleteInvalidMatches(event.matches, event)

        qf_matches = Match.query(Match.event == ndb.Key(Event, '2017scmb'), Match.comp_level == 'qf').fetch()
        self.assertEqual(len(qf_matches), 11)

        sf_matches = Match.query(Match.event == ndb.Key(Event, '2017scmb'), Match.comp_level == 'sf').fetch()
        self.assertEqual(len(sf_matches), 4)

        f_matches = Match.query(Match.event == ndb.Key(Event, '2017scmb'), Match.comp_level == 'f').fetch()
        self.assertEqual(len(f_matches), 3)

        self.assertEqual(Match.get_by_id('2017scmb_qf4m1').alliances['red']['score'], 305)
        self.assertEqual(Match.get_by_id('2017scmb_qf4m1').alliances['blue']['score'], 305)
        self.assertEqual(Match.get_by_id('2017scmb_qf4m1').score_breakdown['red']['totalPoints'], 305)
        self.assertEqual(Match.get_by_id('2017scmb_qf4m1').score_breakdown['blue']['totalPoints'], 305)

        self.assertEqual(Match.get_by_id('2017scmb_qf4m2').alliances['red']['score'], 213)
        self.assertEqual(Match.get_by_id('2017scmb_qf4m2').alliances['blue']['score'], 305)
        self.assertEqual(Match.get_by_id('2017scmb_qf4m2').score_breakdown['red']['totalPoints'], 213)
        self.assertEqual(Match.get_by_id('2017scmb_qf4m2').score_breakdown['blue']['totalPoints'], 305)

        self.assertEqual(Match.get_by_id('2017scmb_qf4m3').alliances['red']['score'], 312)
        self.assertEqual(Match.get_by_id('2017scmb_qf4m3').alliances['blue']['score'], 255)
        self.assertEqual(Match.get_by_id('2017scmb_qf4m3').score_breakdown['red']['totalPoints'], 312)
        self.assertEqual(Match.get_by_id('2017scmb_qf4m3').score_breakdown['blue']['totalPoints'], 255)

        self.assertEqual(Match.get_by_id('2017scmb_qf4m4').alliances['red']['score'], 310)
        self.assertEqual(Match.get_by_id('2017scmb_qf4m4').alliances['blue']['score'], 306)
        self.assertEqual(Match.get_by_id('2017scmb_qf4m4').score_breakdown['red']['totalPoints'], 310)
        self.assertEqual(Match.get_by_id('2017scmb_qf4m4').score_breakdown['blue']['totalPoints'], 306)

    def test_2017scmb(self):
        event = Event(
            id='2017scmb',
            event_short='scmb',
            year=2017,
            event_type_enum=0,
            timezone_id='America/New_York'
        )
        event.put()

        MatchManipulator.createOrUpdate(DatafeedFMSAPI('v2.0', sim_time=datetime.datetime(2017, 3, 04, 19, 17)).getMatches('2017scmb'))
        MatchHelper.deleteInvalidMatches(event.matches, event)
        qf_matches = Match.query(Match.event == ndb.Key(Event, '2017scmb'), Match.comp_level == 'qf').fetch()
        self.assertEqual(len(qf_matches), 12)

        self.assertEqual(Match.get_by_id('2017scmb_qf4m1').alliances['red']['score'], 305)
        self.assertEqual(Match.get_by_id('2017scmb_qf4m1').alliances['blue']['score'], 305)
        self.assertEqual(Match.get_by_id('2017scmb_qf4m1').score_breakdown['red']['totalPoints'], 305)
        self.assertEqual(Match.get_by_id('2017scmb_qf4m1').score_breakdown['blue']['totalPoints'], 305)

        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        MatchManipulator.createOrUpdate(DatafeedFMSAPI('v2.0', sim_time=datetime.datetime(2017, 3, 04, 19, 50)).getMatches('2017scmb'))
        MatchHelper.deleteInvalidMatches(event.matches, event)
        qf_matches = Match.query(Match.event == ndb.Key(Event, '2017scmb'), Match.comp_level == 'qf').fetch()
        self.assertEqual(len(qf_matches), 12)

        self.assertEqual(Match.get_by_id('2017scmb_qf4m1').alliances['red']['score'], 305)
        self.assertEqual(Match.get_by_id('2017scmb_qf4m1').alliances['blue']['score'], 305)
        self.assertEqual(Match.get_by_id('2017scmb_qf4m1').score_breakdown['red']['totalPoints'], 305)
        self.assertEqual(Match.get_by_id('2017scmb_qf4m1').score_breakdown['blue']['totalPoints'], 305)
        self.assertEqual(Match.get_by_id('2017scmb_qf4m2').alliances['red']['score'], 213)
        self.assertEqual(Match.get_by_id('2017scmb_qf4m2').alliances['blue']['score'], 305)
        self.assertEqual(Match.get_by_id('2017scmb_qf4m2').score_breakdown['red']['totalPoints'], 213)
        self.assertEqual(Match.get_by_id('2017scmb_qf4m2').score_breakdown['blue']['totalPoints'], 305)

        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        MatchManipulator.createOrUpdate(DatafeedFMSAPI('v2.0', sim_time=datetime.datetime(2017, 3, 04, 20, 12)).getMatches('2017scmb'))
        MatchHelper.deleteInvalidMatches(event.matches, event)
        qf_matches = Match.query(Match.event == ndb.Key(Event, '2017scmb'), Match.comp_level == 'qf').fetch()
        self.assertEqual(len(qf_matches), 12)

        self.assertEqual(Match.get_by_id('2017scmb_qf4m1').alliances['red']['score'], 305)
        self.assertEqual(Match.get_by_id('2017scmb_qf4m1').alliances['blue']['score'], 305)
        self.assertEqual(Match.get_by_id('2017scmb_qf4m1').score_breakdown['red']['totalPoints'], 305)
        self.assertEqual(Match.get_by_id('2017scmb_qf4m1').score_breakdown['blue']['totalPoints'], 305)
        self.assertEqual(Match.get_by_id('2017scmb_qf4m2').alliances['red']['score'], 213)
        self.assertEqual(Match.get_by_id('2017scmb_qf4m2').alliances['blue']['score'], 305)
        self.assertEqual(Match.get_by_id('2017scmb_qf4m2').score_breakdown['red']['totalPoints'], 213)
        self.assertEqual(Match.get_by_id('2017scmb_qf4m2').score_breakdown['blue']['totalPoints'], 305)
        self.assertEqual(Match.get_by_id('2017scmb_qf4m3').alliances['red']['score'], 312)
        self.assertEqual(Match.get_by_id('2017scmb_qf4m3').alliances['blue']['score'], 255)
        self.assertEqual(Match.get_by_id('2017scmb_qf4m3').score_breakdown['red']['totalPoints'], 312)
        self.assertEqual(Match.get_by_id('2017scmb_qf4m3').score_breakdown['blue']['totalPoints'], 255)

        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        MatchManipulator.createOrUpdate(DatafeedFMSAPI('v2.0', sim_time=datetime.datetime(2017, 3, 04, 20, 48)).getMatches('2017scmb'))
        MatchHelper.deleteInvalidMatches(event.matches, event)
        qf_matches = Match.query(Match.event == ndb.Key(Event, '2017scmb'), Match.comp_level == 'qf').fetch()
        self.assertEqual(len(qf_matches), 13)

        self.assertEqual(Match.get_by_id('2017scmb_qf4m1').alliances['red']['score'], 305)
        self.assertEqual(Match.get_by_id('2017scmb_qf4m1').alliances['blue']['score'], 305)
        self.assertEqual(Match.get_by_id('2017scmb_qf4m1').score_breakdown['red']['totalPoints'], 305)
        self.assertEqual(Match.get_by_id('2017scmb_qf4m1').score_breakdown['blue']['totalPoints'], 305)
        self.assertEqual(Match.get_by_id('2017scmb_qf4m2').alliances['red']['score'], 213)
        self.assertEqual(Match.get_by_id('2017scmb_qf4m2').alliances['blue']['score'], 305)
        self.assertEqual(Match.get_by_id('2017scmb_qf4m2').score_breakdown['red']['totalPoints'], 213)
        self.assertEqual(Match.get_by_id('2017scmb_qf4m2').score_breakdown['blue']['totalPoints'], 305)
        self.assertEqual(Match.get_by_id('2017scmb_qf4m3').alliances['red']['score'], 312)
        self.assertEqual(Match.get_by_id('2017scmb_qf4m3').alliances['blue']['score'], 255)
        self.assertEqual(Match.get_by_id('2017scmb_qf4m3').score_breakdown['red']['totalPoints'], 312)
        self.assertEqual(Match.get_by_id('2017scmb_qf4m3').score_breakdown['blue']['totalPoints'], 255)
        self.assertEqual(Match.get_by_id('2017scmb_qf4m4').alliances['red']['score'], 310)
        self.assertEqual(Match.get_by_id('2017scmb_qf4m4').alliances['blue']['score'], 306)
        self.assertEqual(Match.get_by_id('2017scmb_qf4m4').score_breakdown['red']['totalPoints'], 310)
        self.assertEqual(Match.get_by_id('2017scmb_qf4m4').score_breakdown['blue']['totalPoints'], 306)

    def test_2017ncwin(self):
        event = Event(
            id='2017ncwin',
            event_short='ncwin',
            year=2017,
            event_type_enum=0,
            timezone_id='America/New_York'
        )
        event.put()

        MatchManipulator.createOrUpdate(DatafeedFMSAPI('v2.0', sim_time=datetime.datetime(2017, 3, 05, 21, 2)).getMatches('2017ncwin'))
        MatchHelper.deleteInvalidMatches(event.matches, event)
        sf_matches = Match.query(Match.event == ndb.Key(Event, '2017ncwin'), Match.comp_level == 'sf').fetch()
        self.assertEqual(len(sf_matches), 6)

        self.assertEqual(Match.get_by_id('2017ncwin_sf2m1').alliances['red']['score'], 265)
        self.assertEqual(Match.get_by_id('2017ncwin_sf2m1').alliances['blue']['score'], 150)
        self.assertEqual(Match.get_by_id('2017ncwin_sf2m1').score_breakdown['red']['totalPoints'], 265)
        self.assertEqual(Match.get_by_id('2017ncwin_sf2m1').score_breakdown['blue']['totalPoints'], 150)

        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        MatchManipulator.createOrUpdate(DatafeedFMSAPI('v2.0', sim_time=datetime.datetime(2017, 3, 05, 21, 30)).getMatches('2017ncwin'))
        MatchHelper.deleteInvalidMatches(event.matches, event)
        sf_matches = Match.query(Match.event == ndb.Key(Event, '2017ncwin'), Match.comp_level == 'sf').fetch()
        self.assertEqual(len(sf_matches), 6)

        self.assertEqual(Match.get_by_id('2017ncwin_sf2m1').alliances['red']['score'], 265)
        self.assertEqual(Match.get_by_id('2017ncwin_sf2m1').alliances['blue']['score'], 150)
        self.assertEqual(Match.get_by_id('2017ncwin_sf2m1').score_breakdown['red']['totalPoints'], 265)
        self.assertEqual(Match.get_by_id('2017ncwin_sf2m1').score_breakdown['blue']['totalPoints'], 150)
        self.assertEqual(Match.get_by_id('2017ncwin_sf2m2').alliances['red']['score'], 205)
        self.assertEqual(Match.get_by_id('2017ncwin_sf2m2').alliances['blue']['score'], 205)
        self.assertEqual(Match.get_by_id('2017ncwin_sf2m2').score_breakdown['red']['totalPoints'], 205)
        self.assertEqual(Match.get_by_id('2017ncwin_sf2m2').score_breakdown['blue']['totalPoints'], 205)

        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        MatchManipulator.createOrUpdate(DatafeedFMSAPI('v2.0', sim_time=datetime.datetime(2017, 3, 05, 21, 35)).getMatches('2017ncwin'))
        MatchHelper.deleteInvalidMatches(event.matches, event)
        sf_matches = Match.query(Match.event == ndb.Key(Event, '2017ncwin'), Match.comp_level == 'sf').fetch()
        self.assertEqual(len(sf_matches), 6)

        self.assertEqual(Match.get_by_id('2017ncwin_sf2m1').alliances['red']['score'], 265)
        self.assertEqual(Match.get_by_id('2017ncwin_sf2m1').alliances['blue']['score'], 150)
        self.assertEqual(Match.get_by_id('2017ncwin_sf2m1').score_breakdown['red']['totalPoints'], 265)
        self.assertEqual(Match.get_by_id('2017ncwin_sf2m1').score_breakdown['blue']['totalPoints'], 150)
        self.assertEqual(Match.get_by_id('2017ncwin_sf2m2').alliances['red']['score'], 205)
        self.assertEqual(Match.get_by_id('2017ncwin_sf2m2').alliances['blue']['score'], 205)
        self.assertEqual(Match.get_by_id('2017ncwin_sf2m2').score_breakdown['red']['totalPoints'], 205)
        self.assertEqual(Match.get_by_id('2017ncwin_sf2m2').score_breakdown['blue']['totalPoints'], 205)
        self.assertEqual(Match.get_by_id('2017ncwin_sf2m3').alliances['red']['score'], 145)
        self.assertEqual(Match.get_by_id('2017ncwin_sf2m3').alliances['blue']['score'], 265)
        self.assertEqual(Match.get_by_id('2017ncwin_sf2m3').score_breakdown['red']['totalPoints'], 145)
        self.assertEqual(Match.get_by_id('2017ncwin_sf2m3').score_breakdown['blue']['totalPoints'], 265)

        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        MatchManipulator.createOrUpdate(DatafeedFMSAPI('v2.0', sim_time=datetime.datetime(2017, 3, 05, 21, 51)).getMatches('2017ncwin'))
        MatchHelper.deleteInvalidMatches(event.matches, event)
        sf_matches = Match.query(Match.event == ndb.Key(Event, '2017ncwin'), Match.comp_level == 'sf').fetch()
        self.assertEqual(len(sf_matches), 7)

        self.assertEqual(Match.get_by_id('2017ncwin_sf2m1').alliances['red']['score'], 265)
        self.assertEqual(Match.get_by_id('2017ncwin_sf2m1').alliances['blue']['score'], 150)
        self.assertEqual(Match.get_by_id('2017ncwin_sf2m1').score_breakdown['red']['totalPoints'], 265)
        self.assertEqual(Match.get_by_id('2017ncwin_sf2m1').score_breakdown['blue']['totalPoints'], 150)
        self.assertEqual(Match.get_by_id('2017ncwin_sf2m2').alliances['red']['score'], 205)
        self.assertEqual(Match.get_by_id('2017ncwin_sf2m2').alliances['blue']['score'], 205)
        self.assertEqual(Match.get_by_id('2017ncwin_sf2m2').score_breakdown['red']['totalPoints'], 205)
        self.assertEqual(Match.get_by_id('2017ncwin_sf2m2').score_breakdown['blue']['totalPoints'], 205)
        self.assertEqual(Match.get_by_id('2017ncwin_sf2m3').alliances['red']['score'], 145)
        self.assertEqual(Match.get_by_id('2017ncwin_sf2m3').alliances['blue']['score'], 265)
        self.assertEqual(Match.get_by_id('2017ncwin_sf2m3').score_breakdown['red']['totalPoints'], 145)
        self.assertEqual(Match.get_by_id('2017ncwin_sf2m3').score_breakdown['blue']['totalPoints'], 265)
        self.assertEqual(Match.get_by_id('2017ncwin_sf2m4').alliances['red']['score'], 180)
        self.assertEqual(Match.get_by_id('2017ncwin_sf2m4').alliances['blue']['score'], 305)
        self.assertEqual(Match.get_by_id('2017ncwin_sf2m4').score_breakdown['red']['totalPoints'], 180)
        self.assertEqual(Match.get_by_id('2017ncwin_sf2m4').score_breakdown['blue']['totalPoints'], 305)
