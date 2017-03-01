import datetime
import unittest2
import webtest
import json
import md5

import api_main

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from consts.auth_type import AuthType
from consts.event_type import EventType
from models.account import Account
from models.api_auth_access import ApiAuthAccess
from models.award import Award
from models.event import Event
from models.event_team import EventTeam
from models.match import Match
from models.sitevar import Sitevar
from models.team import Team


class TestApiTrustedController(unittest2.TestCase):

    def setUp(self):
        self.testapp = webtest.TestApp(api_main.app)

        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_urlfetch_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_user_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        self.testbed.init_taskqueue_stub(root_path=".")

        self.teams_auth = ApiAuthAccess(id='tEsT_id_0',
                                        secret='321tEsTsEcReT',
                                        description='test',
                                        event_list=[ndb.Key(Event, '2014casj')],
                                        auth_types_enum=[AuthType.EVENT_TEAMS])

        self.matches_auth = ApiAuthAccess(id='tEsT_id_1',
                                          secret='321tEsTsEcReT',
                                          description='test',
                                          event_list=[ndb.Key(Event, '2014casj')],
                                          auth_types_enum=[AuthType.EVENT_MATCHES])

        self.rankings_auth = ApiAuthAccess(id='tEsT_id_2',
                                           secret='321tEsTsEcReT',
                                           description='test',
                                           event_list=[ndb.Key(Event, '2014casj')],
                                           auth_types_enum=[AuthType.EVENT_RANKINGS])

        self.alliances_auth = ApiAuthAccess(id='tEsT_id_3',
                                            secret='321tEsTsEcReT',
                                            description='test',
                                            event_list=[ndb.Key(Event, '2014casj')],
                                            auth_types_enum=[AuthType.EVENT_ALLIANCES])

        self.awards_auth = ApiAuthAccess(id='tEsT_id_4',
                                         secret='321tEsTsEcReT',
                                         description='test',
                                         event_list=[ndb.Key(Event, '2014casj')],
                                         auth_types_enum=[AuthType.EVENT_AWARDS])

        self.video_auth = ApiAuthAccess(id='tEsT_id_5',
                                        secret='321tEsTsEcReT',
                                        description='test',
                                        event_list=[ndb.Key(Event, '2014casj')],
                                        auth_types_enum=[AuthType.MATCH_VIDEO])

        self.expired_auth = ApiAuthAccess(id='tEsT_id_6',
                                        secret='321tEsTsEcReT',
                                        description='test',
                                        event_list=[ndb.Key(Event, '2014casj')],
                                        auth_types_enum=[AuthType.EVENT_MATCHES],
                                        expiration=datetime.datetime(year=1970, month=1, day=1))

        self.owned_auth = ApiAuthAccess(id='tEsT_id_7',
                                        secret='321tEsTsEcReT',
                                        description='test',
                                        event_list=[ndb.Key(Event, '2014casj')],
                                        auth_types_enum=[AuthType.EVENT_MATCHES],
                                        owner=ndb.Key(Account, "42"))

        self.owned_auth_expired = ApiAuthAccess(id='tEsT_id_8',
                                        secret='321tEsTsEcReT',
                                        description='test',
                                        event_list=[ndb.Key(Event, '2014casj')],
                                        auth_types_enum=[AuthType.EVENT_MATCHES],
                                        owner=ndb.Key(Account, "42"),
                                        expiration=datetime.datetime(year=1970, month=1, day=1))

        self.event = Event(
            id='2014casj',
            event_type_enum=EventType.REGIONAL,
            event_short='casj',
            year=2014,
        )
        self.event.put()

    def tearDown(self):
        self.testbed.deactivate()

    def loginUser(self, is_admin=False):
        self.testbed.setup_env(
            user_email="foo@bar.com",
            user_id="42",
            user_is_admin='1' if is_admin else '0',
            overwrite=True)

    def test_auth(self):
        request_path = '/api/trusted/v1/event/2014casj/matches/update'
        request_path_caps_key = '/api/trusted/v1/event/2014CASJ/matches/update'

        # Fail
        response = self.testapp.post(request_path, expect_errors=True)
        self.assertEqual(response.status_code, 400)
        self.assertTrue('Error' in response.json)

        # Fail
        request_body = json.dumps([])
        sig = md5.new('{}{}{}'.format('321tEsTsEcReT', request_path, request_body)).hexdigest()
        response = self.testapp.post(request_path, request_body, headers={'X-TBA-Auth-Id': 'tEsT_id_1', 'X-TBA-Auth-Sig': sig}, expect_errors=True)
        self.assertEqual(response.status_code, 401)
        self.assertTrue('Error' in response.json)

        self.rankings_auth.put()
        self.matches_auth.put()

        # Pass
        sig = md5.new('{}{}{}'.format('321tEsTsEcReT', request_path, request_body)).hexdigest()
        response = self.testapp.post(request_path, request_body, headers={'X-TBA-Auth-Id': 'tEsT_id_1', 'X-TBA-Auth-Sig': sig}, expect_errors=True)
        self.assertEqual(response.status_code, 200)

        # Pass; all caps key
        sig = md5.new('{}{}{}'.format('321tEsTsEcReT', request_path_caps_key, request_body)).hexdigest()
        response = self.testapp.post(request_path_caps_key, request_body, headers={'X-TBA-Auth-Id': 'tEsT_id_1', 'X-TBA-Auth-Sig': sig}, expect_errors=True)
        self.assertEqual(response.status_code, 200)

        # Fail; bad X-TBA-Auth-Id
        sig = md5.new('{}{}{}'.format('321tEsTsEcReT', request_path, request_body)).hexdigest()
        response = self.testapp.post(request_path, request_body, headers={'X-TBA-Auth-Id': 'badTestAuthId', 'X-TBA-Auth-Sig': sig}, expect_errors=True)
        self.assertEqual(response.status_code, 401)
        self.assertTrue('Error' in response.json)

        # Fail; bad sig
        response = self.testapp.post(request_path, request_body, headers={'X-TBA-Auth-Id': 'tEsT_id_1', 'X-TBA-Auth-Sig': '123abc'}, expect_errors=True)
        self.assertEqual(response.status_code, 401)
        self.assertTrue('Error' in response.json)

        # Fail; bad sig due to wrong body
        body2 = json.dumps([{}])
        sig = md5.new('{}{}{}'.format('321tEsTsEcReT', request_path, request_body)).hexdigest()
        response = self.testapp.post(request_path, body2, headers={'X-TBA-Auth-Id': 'tEsT_id_1', 'X-TBA-Auth-Sig': sig}, expect_errors=True)
        self.assertEqual(response.status_code, 401)
        self.assertTrue('Error' in response.json)

        # Fail; bad event
        request_path2 = '/api/trusted/v1/event/2014cama/matches/update'
        sig = md5.new('{}{}{}'.format('321tEsTsEcReT', request_path2, request_body)).hexdigest()
        response = self.testapp.post(request_path, request_body, headers={'X-TBA-Auth-Id': 'tEsT_id_1', 'X-TBA-Auth-Sig': sig}, expect_errors=True)
        self.assertEqual(response.status_code, 401)
        self.assertTrue('Error' in response.json)

        # Fail; insufficient auth_types_enum
        sig = md5.new('{}{}{}'.format('321tEsTsEcReT', request_path, request_body)).hexdigest()
        response = self.testapp.post(request_path, request_body, headers={'X-TBA-Auth-Id': 'tEsT_id_2', 'X-TBA-Auth-Sig': sig}, expect_errors=True)
        self.assertEqual(response.status_code, 401)
        self.assertTrue('Error' in response.json)

        # Fail; expired keys
        sig = md5.new('{}{}{}'.format('321tEsTsEcReT', request_path, request_body)).hexdigest()
        response = self.testapp.post(request_path, request_body, headers={'X-TBA-Auth-Id': 'tEsT_id_6', 'X-TBA-Auth-Sig': sig}, expect_errors=True)
        self.assertEqual(response.status_code, 401)
        self.assertTrue('Error' in response.json)

    def test_admin_auth(self):
        # Ensure that a logged in admin user can access any evet
        request_path = '/api/trusted/v1/event/2014casj/matches/update'
        request_body = json.dumps([])
        self.loginUser(is_admin=True)

        response = self.testapp.post(request_path, request_body, expect_errors=True)
        self.assertEqual(response.status_code, 200)

    def test_user_auth(self):
        # Ensure that a logged in user can use auths granted to their account
        request_path = '/api/trusted/v1/event/2014casj/matches/update'
        request_body = json.dumps([])
        self.owned_auth.put()
        self.loginUser()

        response = self.testapp.post(request_path, request_body, expect_errors=True)
        self.assertEqual(response.status_code, 200)

    def test_user_expired_auth(self):
        # Ensure that a logged in user can use auths granted to their account
        request_path = '/api/trusted/v1/event/2014casj/matches/update'
        request_body = json.dumps([])
        self.owned_auth_expired.put()
        self.loginUser()

        # Should end up with a 400 error because the expired key didn't count and no explicit
        # Auth-Id header was passed
        response = self.testapp.post(request_path, request_body, expect_errors=True)
        self.assertEqual(response.status_code, 400)
        self.assertTrue('Error' in response.json)

    def test_killswitch(self):
        request_path = '/api/trusted/v1/event/2014casj/matches/update'
        request_body = json.dumps([])

        # Pass
        self.matches_auth.put()
        sig = md5.new('{}{}{}'.format('321tEsTsEcReT', request_path, request_body)).hexdigest()
        response = self.testapp.post(request_path, request_body, headers={'X-TBA-Auth-Id': 'tEsT_id_1', 'X-TBA-Auth-Sig': sig}, expect_errors=True)
        self.assertEqual(response.status_code, 200)

        # Now, set the disable sitevar
        trusted_sitevar = Sitevar(
            id='trustedapi',
            values_json=json.dumps({
                3: False,
            })
        )
        trusted_sitevar.put()

        # Fail
        sig = md5.new('{}{}{}'.format('321tEsTsEcReT', request_path, request_body)).hexdigest()
        response = self.testapp.post(request_path, request_body, headers={'X-TBA-Auth-Id': 'tEsT_id_1', 'X-TBA-Auth-Sig': sig}, expect_errors=True)
        self.assertEqual(response.status_code, 401)

    def test_alliance_selections_update(self):
        self.alliances_auth.put()

        alliances = [['frc971', 'frc254', 'frc1662'],
                     ['frc1678', 'frc368', 'frc4171'],
                     ['frc2035', 'frc192', 'frc4990'],
                     ['frc1323', 'frc846', 'frc2135'],
                     ['frc2144', 'frc1388', 'frc668'],
                     ['frc1280', 'frc604', 'frc100'],
                     ['frc114', 'frc852', 'frc841'],
                     ['frc2473', 'frc3256', 'frc1868']]
        request_body = json.dumps(alliances)

        request_path = '/api/trusted/v1/event/2014casj/alliance_selections/update'
        sig = md5.new('{}{}{}'.format('321tEsTsEcReT', request_path, request_body)).hexdigest()
        response = self.testapp.post(request_path, request_body, headers={'X-TBA-Auth-Id': 'tEsT_id_3', 'X-TBA-Auth-Sig': sig}, expect_errors=True)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(self.event.alliance_selections), 8)
        for i, selection in enumerate(self.event.alliance_selections):
            self.assertEqual(alliances[i], selection['picks'])

    def test_empty_alliance_selections_update(self):
        self.alliances_auth.put()

        alliances = [['frc971', 'frc254', 'frc1662'],
                     ['frc1678', 'frc368', 'frc4171'],
                     ['frc2035', 'frc192', 'frc4990'],
                     ['frc1323', 'frc846', 'frc2135'],
                     [],[],[],[]]
        request_body = json.dumps(alliances)

        request_path = '/api/trusted/v1/event/2014casj/alliance_selections/update'
        sig = md5.new('{}{}{}'.format('321tEsTsEcReT', request_path, request_body)).hexdigest()
        response = self.testapp.post(request_path, request_body, headers={'X-TBA-Auth-Id': 'tEsT_id_3', 'X-TBA-Auth-Sig': sig}, expect_errors=True)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(self.event.alliance_selections), 4)
        for i, selection in enumerate(self.event.alliance_selections):
            self.assertEqual(alliances[i], selection['picks'])

    def test_awards_update(self):
        self.awards_auth.put()

        awards = [{'name_str': 'Winner', 'team_key': 'frc254'},
                  {'name_str': 'Winner', 'team_key': 'frc604'},
                  {'name_str': 'Volunteer Blahblah', 'team_key': 'frc1', 'awardee': 'Bob Bobby'}]
        request_body = json.dumps(awards)

        request_path = '/api/trusted/v1/event/2014casj/awards/update'
        sig = md5.new('{}{}{}'.format('321tEsTsEcReT', request_path, request_body)).hexdigest()
        response = self.testapp.post(request_path, request_body, headers={'X-TBA-Auth-Id': 'tEsT_id_4', 'X-TBA-Auth-Sig': sig}, expect_errors=True)

        self.assertEqual(response.status_code, 200)

        db_awards = Award.query(Award.event == self.event.key).fetch(None)
        self.assertEqual(len(db_awards), 2)
        self.assertTrue('2014casj_1' in [a.key.id() for a in db_awards])
        self.assertTrue('2014casj_5' in [a.key.id() for a in db_awards])

        awards = [{'name_str': 'Winner', 'team_key': 'frc254'},
                  {'name_str': 'Winner', 'team_key': 'frc604'}]
        request_body = json.dumps(awards)

        sig = md5.new('{}{}{}'.format('321tEsTsEcReT', request_path, request_body)).hexdigest()
        response = self.testapp.post(request_path, request_body, headers={'X-TBA-Auth-Id': 'tEsT_id_4', 'X-TBA-Auth-Sig': sig}, expect_errors=True)

        self.assertEqual(response.status_code, 200)

        db_awards = Award.query(Award.event == self.event.key).fetch(None)
        self.assertEqual(len(db_awards), 1)
        self.assertTrue('2014casj_1' in [a.key.id() for a in db_awards])

    def test_matches_update(self):
        self.matches_auth.put()

        update_request_path = '/api/trusted/v1/event/2014casj/matches/update'
        delete_request_path = '/api/trusted/v1/event/2014casj/matches/delete'
        delete_all_request_path = '/api/trusted/v1/event/2014casj/matches/delete_all'

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
            },
            'time_string': '9:00 AM',
            'time_utc': '2014-08-31T16:00:00',
        }]
        request_body = json.dumps(matches)
        sig = md5.new('{}{}{}'.format('321tEsTsEcReT', update_request_path, request_body)).hexdigest()
        response = self.testapp.post(update_request_path, request_body, headers={'X-TBA-Auth-Id': 'tEsT_id_1', 'X-TBA-Auth-Sig': sig}, expect_errors=True)

        self.assertEqual(response.status_code, 200)

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
            },
            'time_string': '10:00 AM',
            'time_utc': '2014-08-31T17:00:00',
        }]
        request_body = json.dumps(matches)
        sig = md5.new('{}{}{}'.format('321tEsTsEcReT', update_request_path, request_body)).hexdigest()
        response = self.testapp.post(update_request_path, request_body, headers={'X-TBA-Auth-Id': 'tEsT_id_1', 'X-TBA-Auth-Sig': sig}, expect_errors=True)
        self.assertEqual(response.status_code, 200)

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
            },
            'score_breakdown': {
                'red': {'auto': 20, 'assist': 40, 'truss+catch': 20, 'teleop_goal+foul': 20},
                'blue': {'auto': 40, 'assist': 60, 'truss+catch': 10, 'teleop_goal+foul': 40},
            },
            'time_string': '11:00 AM',
            'time_utc': '2014-08-31T18:00:00',
        }]
        request_body = json.dumps(matches)
        sig = md5.new('{}{}{}'.format('321tEsTsEcReT', update_request_path, request_body)).hexdigest()
        response = self.testapp.post(update_request_path, request_body, headers={'X-TBA-Auth-Id': 'tEsT_id_1', 'X-TBA-Auth-Sig': sig}, expect_errors=True)
        self.assertEqual(response.status_code, 200)

        keys_to_delete = ['qm1']
        request_body = json.dumps(keys_to_delete)
        sig = md5.new('{}{}{}'.format('321tEsTsEcReT', delete_request_path, request_body)).hexdigest()
        response = self.testapp.post(delete_request_path, request_body, headers={'X-TBA-Auth-Id': 'tEsT_id_1', 'X-TBA-Auth-Sig': sig}, expect_errors=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['keys_deleted'], ['qm1'])

        db_matches = Match.query(Match.event == self.event.key).fetch(None)
        self.assertEqual(len(db_matches), 2)
        self.assertTrue('2014casj_f1m1' in [m.key.id() for m in db_matches])
        self.assertTrue('2014casj_f1m2' in [m.key.id() for m in db_matches])

        db_matches = Match.query(Match.event == self.event.key).fetch(None)
        self.assertEqual(len(db_matches), 2)
        self.assertTrue('2014casj_f1m1' in [m.key.id() for m in db_matches])
        self.assertTrue('2014casj_f1m2' in [m.key.id() for m in db_matches])

        # verify match data
        match = Match.get_by_id('2014casj_f1m2')
        self.assertEqual(match.time, datetime.datetime(2014, 8, 31, 18, 0))
        self.assertEqual(match.time_string, '11:00 AM')
        self.assertEqual(match.alliances['red']['score'], 250)
        self.assertEqual(match.score_breakdown['red']['truss+catch'], 20)

        # test delete all matches
        request_body = ''
        sig = md5.new('{}{}{}'.format('321tEsTsEcReT', delete_all_request_path, request_body)).hexdigest()
        response = self.testapp.post(delete_all_request_path, request_body, headers={'X-TBA-Auth-Id': 'tEsT_id_1', 'X-TBA-Auth-Sig': sig}, expect_errors=True)
        self.assertEqual(response.status_code, 400)

        request_body = '2014casj'
        sig = md5.new('{}{}{}'.format('321tEsTsEcReT', delete_all_request_path, request_body)).hexdigest()
        response = self.testapp.post(delete_all_request_path, request_body, headers={'X-TBA-Auth-Id': 'tEsT_id_1', 'X-TBA-Auth-Sig': sig}, expect_errors=True)
        self.assertEqual(response.status_code, 200)

        db_matches = Match.query(Match.event == self.event.key).fetch(None)
        self.assertEqual(len(db_matches), 0)

    def test_rankings_update(self):
        self.rankings_auth.put()

        rankings = {
            'breakdowns': ['QS', 'Auton', 'Teleop', 'T&C'],
            'rankings': [
                {'team_key': 'frc254', 'rank': 1, 'played': 10, 'dqs': 0, 'QS': 20, 'Auton': 500, 'Teleop': 500, 'T&C': 200},
                {'team_key': 'frc971', 'rank': 2, 'played': 10, 'dqs': 0, 'QS': 20, 'Auton': 500, 'Teleop': 500, 'T&C': 200}
            ],
        }
        request_body = json.dumps(rankings)

        request_path = '/api/trusted/v1/event/2014casj/rankings/update'
        sig = md5.new('{}{}{}'.format('321tEsTsEcReT', request_path, request_body)).hexdigest()
        response = self.testapp.post(request_path, request_body, headers={'X-TBA-Auth-Id': 'tEsT_id_2', 'X-TBA-Auth-Sig': sig}, expect_errors=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.event.rankings[0], ['Rank', 'Team', 'QS', 'Auton', 'Teleop', 'T&C', 'DQ', 'Played'])
        self.assertEqual(self.event.rankings[1], [1, '254', 20, 500, 500, 200, 0, 10])

    def test_rankings_wlt_update(self):
        self.rankings_auth.put()

        rankings = {
            'breakdowns': ['QS', 'Auton', 'Teleop', 'T&C', 'wins', 'losses', 'ties'],
            'rankings': [
                {'team_key': 'frc254', 'rank': 1, 'wins': 10, 'losses': 0, 'ties': 0, 'played': 10, 'dqs': 0, 'QS': 20, 'Auton': 500, 'Teleop': 500, 'T&C': 200},
                {'team_key': 'frc971', 'rank': 2, 'wins': 10, 'losses': 0, 'ties': 0, 'played': 10, 'dqs': 0, 'QS': 20, 'Auton': 500, 'Teleop': 500, 'T&C': 200}
            ],
        }
        request_body = json.dumps(rankings)

        request_path = '/api/trusted/v1/event/2014casj/rankings/update'
        sig = md5.new('{}{}{}'.format('321tEsTsEcReT', request_path, request_body)).hexdigest()
        response = self.testapp.post(request_path, request_body, headers={'X-TBA-Auth-Id': 'tEsT_id_2', 'X-TBA-Auth-Sig': sig}, expect_errors=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.event.rankings[0], ['Rank', 'Team', 'QS', 'Auton', 'Teleop', 'T&C', 'Record (W-L-T)', 'DQ', 'Played'])
        self.assertEqual(self.event.rankings[1], [1, '254', 20, 500, 500, 200, '10-0-0', 0, 10])

    def test_eventteams_update(self):
        self.teams_auth.put()

        team_list = ['frc254', 'frc971', 'frc604']
        request_body = json.dumps(team_list)

        # Insert teams into db, otherwise they won't get added (see 072058b)
        Team(id='frc254', team_number=254).put()
        Team(id='frc971', team_number=971).put()
        Team(id='frc604', team_number=604).put()
        Team(id='frc100', team_number=100).put()

        request_path = '/api/trusted/v1/event/2014casj/team_list/update'
        sig = md5.new('{}{}{}'.format('321tEsTsEcReT', request_path, request_body)).hexdigest()
        response = self.testapp.post(request_path, request_body, headers={'X-TBA-Auth-Id': 'tEsT_id_0', 'X-TBA-Auth-Sig': sig}, expect_errors=True)

        self.assertEqual(response.status_code, 200)

        db_eventteams = EventTeam.query(EventTeam.event == self.event.key).fetch(None)
        self.assertEqual(len(db_eventteams), 3)
        self.assertTrue('2014casj_frc254' in [et.key.id() for et in db_eventteams])
        self.assertTrue('2014casj_frc971' in [et.key.id() for et in db_eventteams])
        self.assertTrue('2014casj_frc604' in [et.key.id() for et in db_eventteams])

        team_list = ['frc254', 'frc100']
        request_body = json.dumps(team_list)

        sig = md5.new('{}{}{}'.format('321tEsTsEcReT', request_path, request_body)).hexdigest()
        response = self.testapp.post(request_path, request_body, headers={'X-TBA-Auth-Id': 'tEsT_id_0', 'X-TBA-Auth-Sig': sig}, expect_errors=True)

        self.assertEqual(response.status_code, 200)

        db_eventteams = EventTeam.query(EventTeam.event == self.event.key).fetch(None)
        self.assertEqual(len(db_eventteams), 2)
        self.assertTrue('2014casj_frc254' in [et.key.id() for et in db_eventteams])
        self.assertTrue('2014casj_frc100' in [et.key.id() for et in db_eventteams])

    def test_eventteams_unknown(self):
        self.teams_auth.put()

        team_list = ['frc254', 'frc971', 'frc604']
        request_body = json.dumps(team_list)

        # Insert teams into db, otherwise they won't get added (see 072058b)
        Team(id='frc254', team_number=254).put()
        Team(id='frc971', team_number=971).put()

        request_path = '/api/trusted/v1/event/2014casj/team_list/update'
        sig = md5.new('{}{}{}'.format('321tEsTsEcReT', request_path, request_body)).hexdigest()
        response = self.testapp.post(request_path, request_body, headers={'X-TBA-Auth-Id': 'tEsT_id_0', 'X-TBA-Auth-Sig': sig}, expect_errors=True)

        self.assertEqual(response.status_code, 200)

        db_eventteams = EventTeam.query(EventTeam.event == self.event.key).fetch(None)
        self.assertEqual(len(db_eventteams), 2)
        self.assertTrue('2014casj_frc254' in [et.key.id() for et in db_eventteams])
        self.assertTrue('2014casj_frc971' in [et.key.id() for et in db_eventteams])
        self.assertTrue('2014casj_frc604' not in [et.key.id() for et in db_eventteams])

        team_list = ['frc254', 'frc100']
        request_body = json.dumps(team_list)

        sig = md5.new('{}{}{}'.format('321tEsTsEcReT', request_path, request_body)).hexdigest()
        response = self.testapp.post(request_path, request_body, headers={'X-TBA-Auth-Id': 'tEsT_id_0', 'X-TBA-Auth-Sig': sig}, expect_errors=True)

        self.assertEqual(response.status_code, 200)

        db_eventteams = EventTeam.query(EventTeam.event == self.event.key).fetch(None)
        self.assertEqual(len(db_eventteams), 1)
        self.assertTrue('2014casj_frc254' in [et.key.id() for et in db_eventteams])
        self.assertTrue('2014casj_frc100' not in [et.key.id() for et in db_eventteams])

    def test_match_videos_add(self):
        self.video_auth.put()

        match1 = Match(
            id="2014casj_qm1",
            alliances_json="""{"blue": {"score": -1, "teams": ["frc3464", "frc20", "frc1073"]}, "red": {"score": -1, "teams": ["frc69", "frc571", "frc176"]}}""",
            comp_level="qm",
            event=ndb.Key(Event, '2014casj'),
            year=2014,
            set_number=1,
            match_number=1,
            team_key_names=[u'frc69', u'frc571', u'frc176', u'frc3464', u'frc20', u'frc1073'],
            youtube_videos=["abcdef"]
        )
        match1.put()

        match2 = Match(
            id="2014casj_sf1m1",
            alliances_json="""{"blue": {"score": -1, "teams": ["frc3464", "frc20", "frc1073"]}, "red": {"score": -1, "teams": ["frc69", "frc571", "frc176"]}}""",
            comp_level="sf",
            event=ndb.Key(Event, '2014casj'),
            year=2014,
            set_number=1,
            match_number=1,
            team_key_names=[u'frc69', u'frc571', u'frc176', u'frc3464', u'frc20', u'frc1073'],
        )
        match2.put()

        match_videos = {'qm1': 'aFZy8iibMD0', 'sf1m1': 'RpSgUrsghv4'}

        request_body = json.dumps(match_videos)

        request_path = '/api/trusted/v1/event/2014casj/match_videos/add'
        sig = md5.new('{}{}{}'.format('321tEsTsEcReT', request_path, request_body)).hexdigest()
        response = self.testapp.post(request_path, request_body, headers={'X-TBA-Auth-Id': 'tEsT_id_5', 'X-TBA-Auth-Sig': sig}, expect_errors=True)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(set(Match.get_by_id('2014casj_qm1').youtube_videos), {'abcdef', 'aFZy8iibMD0'})
        self.assertEqual(set(Match.get_by_id('2014casj_sf1m1').youtube_videos), {'RpSgUrsghv4'})
