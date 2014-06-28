import unittest2
import webtest
import json
import webapp2

import api_main

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from consts.event_type import EventType

from controllers.api.api_event_controller import ApiEventController

from models.api_auth_access import ApiAuthAccess
from models.award import Award
from models.event import Event
from models.event_team import EventTeam
from models.match import Match


class TestApiTrustedController(unittest2.TestCase):
    def setUp(self):
        self.testapp = webtest.TestApp(api_main.app)

        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_urlfetch_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_taskqueue_stub()

        self.aaa = ApiAuthAccess(id='TeStAuThId123',
                                 secret='321tEsTsEcReT',
                                 description='test',
                                 event_list=[ndb.Key(Event, '2014casj')])

        self.event = Event(
                id='2014casj',
                event_type_enum=EventType.REGIONAL,
                event_short='casj',
                year=2014,
        )
        self.event.put()

    def tearDown(self):
        self.testbed.deactivate()

    def test_auth(self):
        # Fail
        response = self.testapp.post('/api/trusted/v1/event/2014casj/matches/update', expect_errors=True)
        self.assertEqual(response.status_code, 400)
        self.assertTrue('Error' in response.json)

        # Fail
        response = self.testapp.post('/api/trusted/v1/event/2014casj/matches/update', {'auth-id': 'TeStAuThId123', 'secret': '321tEsTsEcReT', 'matches': json.dumps([])}, expect_errors=True)
        self.assertEqual(response.status_code, 400)
        self.assertTrue('Error' in response.json)

        self.aaa.put()

        # Pass
        response = self.testapp.post('/api/trusted/v1/event/2014casj/matches/update', {'auth-id': 'TeStAuThId123', 'secret': '321tEsTsEcReT', 'matches': json.dumps([])}, expect_errors=True)
        self.assertEqual(response.status_code, 200)

        # Fail; bad auth-id
        response = self.testapp.post('/api/trusted/v1/event/2014casj/matches/update', {'auth-id': 'TeStAuThId1231', 'secret': '321tEsTsEcReT', 'matches': json.dumps([])}, expect_errors=True)
        self.assertEqual(response.status_code, 400)
        self.assertTrue('Error' in response.json)

        # Fail; bad secret
        response = self.testapp.post('/api/trusted/v1/event/2014casj/matches/update', {'auth-id': 'TeStAuThId123', 'secret': '321tEsTsEcReT1', 'matches': json.dumps([])}, expect_errors=True)
        self.assertEqual(response.status_code, 400)
        self.assertTrue('Error' in response.json)

        # Fail; bad event
        response = self.testapp.post('/api/trusted/v1/event/2014cama/matches/update', {'auth-id': 'TeStAuThId123', 'secret': '321tEsTsEcReT', 'matches': json.dumps([])}, expect_errors=True)
        self.assertEqual(response.status_code, 400)
        self.assertTrue('Error' in response.json)

    def test_alliance_selections_update(self):
        self.aaa.put()

        alliances = [['frc971', 'frc254', 'frc1662'],
                     ['frc1678', 'frc368', 'frc4171'],
                     ['frc2035', 'frc192', 'frc4990'],
                     ['frc1323', 'frc846', 'frc2135'],
                     ['frc2144', 'frc1388', 'frc668'],
                     ['frc1280', 'frc604', 'frc100'],
                     ['frc114', 'frc852', 'frc841'],
                     ['frc2473', 'frc3256', 'frc1868']]
        response = self.testapp.post('/api/trusted/v1/event/2014casj/alliance_selections/update', {'auth-id': 'TeStAuThId123', 'secret': '321tEsTsEcReT', 'alliances': json.dumps(alliances)}, expect_errors=True)
        self.assertEqual(response.status_code, 200)
        for i, selection in enumerate(self.event.alliance_selections):
            self.assertEqual(alliances[i], selection['picks'])

    def test_awards_update(self):
        self.aaa.put()

        awards = [{'name_str': 'Winner', 'team_key': 'frc254'},
                  {'name_str': 'Winner', 'team_key': 'frc604'},
                  {'name_str': 'Volunteer Blahblah', 'team_key': 'frc1', 'awardee': 'Bob Bobby'}]
        response = self.testapp.post('/api/trusted/v1/event/2014casj/awards/update', {'auth-id': 'TeStAuThId123', 'secret': '321tEsTsEcReT', 'awards': json.dumps(awards)}, expect_errors=True)
        self.assertEqual(response.status_code, 200)

        db_awards = Award.query(Award.event == self.event.key).fetch(None)
        self.assertEqual(len(db_awards), 2)
        self.assertTrue('2014casj_1' in [a.key.id() for a in db_awards])
        self.assertTrue('2014casj_5' in [a.key.id() for a in db_awards])

        awards = [{'name_str': 'Winner', 'team_key': 'frc254'},
                  {'name_str': 'Winner', 'team_key': 'frc604'}]
        response = self.testapp.post('/api/trusted/v1/event/2014casj/awards/update', {'auth-id': 'TeStAuThId123', 'secret': '321tEsTsEcReT', 'awards': json.dumps(awards)}, expect_errors=True)
        self.assertEqual(response.status_code, 200)

        db_awards = Award.query(Award.event == self.event.key).fetch(None)
        self.assertEqual(len(db_awards), 1)
        self.assertTrue('2014casj_1' in [a.key.id() for a in db_awards])

    def test_matches_update(self):
        self.aaa.put()

        # add one match
        matches = [{
            'comp_level': 'qm',
            'set_number': 1,
            'match_number': 1,
            'alliances': {
                'red': {'teams': ['frc1', 'frc2', 'frc3'],
                        'score': 25},
                'blue': {'teams': ['frc4', 'frc5', 'frc6'],
                        'score': 26},
            }
        }]
        response = self.testapp.post('/api/trusted/v1/event/2014casj/matches/update', {'auth-id': 'TeStAuThId123', 'secret': '321tEsTsEcReT', 'matches': json.dumps(matches)}, expect_errors=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['keys_deleted'], [])

        db_matches = Match.query(Match.event == self.event.key).fetch(None)
        self.assertEqual(len(db_matches), 1)
        self.assertTrue('2014casj_qm1' in [m.key.id() for m in db_matches])

        # add another match
        matches = [{
            'comp_level': 'f',
            'set_number': 1,
            'match_number': 1,
            'alliances': {
                'red': {'teams': ['frc1', 'frc2', 'frc3'],
                        'score': 250},
                'blue': {'teams': ['frc4', 'frc5', 'frc6'],
                        'score': 260},
            }
        }]
        response = self.testapp.post('/api/trusted/v1/event/2014casj/matches/update', {'auth-id': 'TeStAuThId123', 'secret': '321tEsTsEcReT', 'matches': json.dumps(matches)}, expect_errors=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['keys_deleted'], [])

        db_matches = Match.query(Match.event == self.event.key).fetch(None)
        self.assertEqual(len(db_matches), 2)
        self.assertTrue('2014casj_qm1' in [m.key.id() for m in db_matches])
        self.assertTrue('2014casj_f1m1' in [m.key.id() for m in db_matches])

        # add a match and delete a match
        matches = [{
            'comp_level': 'f',
            'set_number': 1,
            'match_number': 2,
            'alliances': {
                'red': {'teams': ['frc1', 'frc2', 'frc3'],
                        'score': 250},
                'blue': {'teams': ['frc4', 'frc5', 'frc6'],
                        'score': 260},
            }
        }]
        keys_to_delete = ['2014casj_qm1']
        response = self.testapp.post(
            '/api/trusted/v1/event/2014casj/matches/update', {'auth-id': 'TeStAuThId123', 'secret': '321tEsTsEcReT',
            'matches': json.dumps(matches), 'keys_to_delete': json.dumps(keys_to_delete)}, expect_errors=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['keys_deleted'], ['2014casj_qm1'])

        db_matches = Match.query(Match.event == self.event.key).fetch(None)
        self.assertEqual(len(db_matches), 2)
        self.assertTrue('2014casj_f1m1' in [m.key.id() for m in db_matches])
        self.assertTrue('2014casj_f1m2' in [m.key.id() for m in db_matches])

        # delete a match from unauthorized event
        matches = []
        keys_to_delete = ['2014cama_f1m1']
        response = self.testapp.post(
            '/api/trusted/v1/event/2014casj/matches/update', {'auth-id': 'TeStAuThId123', 'secret': '321tEsTsEcReT',
            'matches': json.dumps(matches), 'keys_to_delete': json.dumps(keys_to_delete)}, expect_errors=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['keys_deleted'], [])

        db_matches = Match.query(Match.event == self.event.key).fetch(None)
        self.assertEqual(len(db_matches), 2)
        self.assertTrue('2014casj_f1m1' in [m.key.id() for m in db_matches])
        self.assertTrue('2014casj_f1m2' in [m.key.id() for m in db_matches])

    def test_rankings_update(self):
        self.aaa.put()

        rankings = {
            'breakdowns': ['QS', 'Auton', 'Teleop', 'T&C'],
            'rankings': [
                {'team_key': 'frc254', 'rank': 1, 'wins': 10, 'losses': 0, 'ties': 0, 'played': 10, 'dqs': 0, 'QS': 20, 'Auton': 500, 'Teleop': 500, 'T&C': 200},
                {'team_key': 'frc971', 'rank': 2, 'wins': 10, 'losses': 0, 'ties': 0, 'played': 10, 'dqs': 0, 'QS': 20, 'Auton': 500, 'Teleop': 500, 'T&C': 200}
            ],
        }
        response = self.testapp.post('/api/trusted/v1/event/2014casj/rankings/update', {'auth-id': 'TeStAuThId123', 'secret': '321tEsTsEcReT', 'rankings': json.dumps(rankings)}, expect_errors=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.event.rankings[0], ['Rank', 'Team', 'QS', 'Auton', 'Teleop', 'T&C', 'Record (W-L-T)', 'DQ', 'Played'])
        self.assertEqual(self.event.rankings[1], [1, '254', 20, 500, 500, 200, '10-0-0', 0, 10])

    def test_eventteams_update(self):
        self.aaa.put()

        team_list = ['frc254', 'frc971', 'frc604']
        response = self.testapp.post('/api/trusted/v1/event/2014casj/team_list/update', {'auth-id': 'TeStAuThId123', 'secret': '321tEsTsEcReT', 'team_list': json.dumps(team_list)}, expect_errors=True)
        self.assertEqual(response.status_code, 200)

        db_eventteams = EventTeam.query(EventTeam.event == self.event.key).fetch(None)
        self.assertEqual(len(db_eventteams), 3)
        self.assertTrue('2014casj_frc254' in [et.key.id() for et in db_eventteams])
        self.assertTrue('2014casj_frc971' in [et.key.id() for et in db_eventteams])
        self.assertTrue('2014casj_frc604' in [et.key.id() for et in db_eventteams])

        team_list = ['frc254', 'frc100']
        response = self.testapp.post('/api/trusted/v1/event/2014casj/team_list/update', {'auth-id': 'TeStAuThId123', 'secret': '321tEsTsEcReT', 'team_list': json.dumps(team_list)}, expect_errors=True)
        self.assertEqual(response.status_code, 200)

        db_eventteams = EventTeam.query(EventTeam.event == self.event.key).fetch(None)
        self.assertEqual(len(db_eventteams), 2)
        self.assertTrue('2014casj_frc254' in [et.key.id() for et in db_eventteams])
        self.assertTrue('2014casj_frc100' in [et.key.id() for et in db_eventteams])
