import copy
import datetime
import unittest2
import webtest
import json
import md5

import api_main
import cron_main

from google.appengine.api import taskqueue
from google.appengine.ext import ndb
from google.appengine.ext import testbed

from consts.account_permissions import AccountPermissions
from consts.auth_type import AuthType
from consts.event_type import EventType
from consts.media_type import MediaType
from consts.playoff_type import PlayoffType
from models.account import Account
from models.api_auth_access import ApiAuthAccess
from models.award import Award
from models.event import Event
from models.event_team import EventTeam
from models.match import Match
from models.media import Media
from models.sitevar import Sitevar
from models.team import Team
from models.zebra_motionworks import ZebraMotionWorks


class TestApiTrustedController(unittest2.TestCase):
    def setUp(self):
        self.testapp = webtest.TestApp(api_main.app)
        self.cronapp = webtest.TestApp(cron_main.app)

        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_urlfetch_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_user_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        self.testbed.init_taskqueue_stub(root_path=".")
        self.taskqueue_stub = self.testbed.get_stub(testbed.TASKQUEUE_SERVICE_NAME)

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

        self.event_info_auth = ApiAuthAccess(id='tEsT_id_9',
                                             secret='321tEsTsEcReT',
                                             description='test',
                                             event_list=[ndb.Key(Event, '2014casj')],
                                             auth_types_enum=[AuthType.EVENT_INFO])

        self.event_zebra_motionworks = ApiAuthAccess(id='tEsT_id_10',
                                                     secret='321tEsTsEcReT',
                                                     description='test',
                                                     event_list=[ndb.Key(Event, '2014casj')],
                                                     auth_types_enum=[AuthType.ZEBRA_MOTIONWORKS])

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

    def grantPermission(self, permission):
        self.account = Account(id="42", permissions=[permission])
        self.account.put()

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

    def test_user_permission(self):
        self.loginUser()
        self.grantPermission(AccountPermissions.OFFSEASON_EVENTWIZARD)

        # This should only work for current year offseasons
        self.event.year = datetime.datetime.now().year
        self.event.event_type_enum = EventType.OFFSEASON
        self.event.put()

        request_path = '/api/trusted/v1/event/2014casj/matches/update'
        request_body = json.dumps([])
        response = self.testapp.post(request_path, request_body, expect_errors=True)
        self.assertEqual(response.status_code, 200)

    def test_user_permission_fail_not_current_year(self):
        self.loginUser()
        self.grantPermission(AccountPermissions.OFFSEASON_EVENTWIZARD)

        # This should only work for current year offseasons
        self.event.year = 2012  # Unless this runs in a time machine...
        self.event.event_type_enum = EventType.OFFSEASON
        self.event.put()

        request_path = '/api/trusted/v1/event/2014casj/matches/update'
        request_body = json.dumps([])
        response = self.testapp.post(request_path, request_body, expect_errors=True)
        self.assertEqual(response.status_code, 400)

    def test_user_permission_fail_not_offseason_event(self):
        self.loginUser()
        self.grantPermission(AccountPermissions.OFFSEASON_EVENTWIZARD)

        # This should only work for current year offseasons
        self.event.year = datetime.datetime.now().year
        self.event.event_type_enum = EventType.REGIONAL
        self.event.put()

        request_path = '/api/trusted/v1/event/2014casj/matches/update'
        request_body = json.dumps([])
        response = self.testapp.post(request_path, request_body, expect_errors=True)
        self.assertEqual(response.status_code, 400)

    def test_user_permission_fail_not_granted(self):
        self.loginUser()

        # This should only work for current year offseasons
        self.event.year = datetime.datetime.now().year
        self.event.event_type_enum = EventType.OFFSEASON
        self.event.put()

        request_path = '/api/trusted/v1/event/2014casj/matches/update'
        request_body = json.dumps([])
        response = self.testapp.post(request_path, request_body, expect_errors=True)
        self.assertEqual(response.status_code, 400)

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
                     [], [], [], []]
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
                        'score': 250,
                        'surrogates': ['frc1'],
                        'dqs': ['frc2']},
                'blue': {'teams': ['frc4', 'frc5', 'frc6'],
                         'score': 260,
                         'surrogates': [],
                         'dqs': []},
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
        self.assertEqual(match.alliances['red']['teams'], ['frc1', 'frc2', 'frc3'])
        self.assertEqual(match.alliances['red']['score'], 250)
        self.assertEqual(match.alliances['red']['surrogates'], ['frc1'])
        self.assertEqual(match.alliances['red']['dqs'], ['frc1', 'frc2', 'frc3'])
        self.assertEqual(match.score_breakdown['red']['truss+catch'], 20)
        self.assertEqual(match.alliances['blue']['teams'], ['frc4', 'frc5', 'frc6'])
        self.assertEqual(match.alliances['blue']['score'], 260)
        self.assertEqual(match.alliances['blue']['surrogates'], [])
        self.assertEqual(match.alliances['blue']['dqs'], [])

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

    def test_event_media_add(self):
        self.video_auth.put()

        event = Event(
            id='2014casj',
            event_type_enum=EventType.REGIONAL,
            event_short='casj',
            year=2014,
        )
        event.put()

        videos = ['aFZy8iibMD0']
        request_body = json.dumps(videos)
        request_path = '/api/trusted/v1/event/2014casj/media/add'
        sig = md5.new('{}{}{}'.format('321tEsTsEcReT', request_path, request_body)).hexdigest()
        response = self.testapp.post(request_path, request_body, headers={'X-TBA-Auth-Id': 'tEsT_id_5', 'X-TBA-Auth-Sig': sig}, expect_errors=True)

        self.assertEqual(response.status_code, 200)

        media_key = Media.render_key_name(MediaType.YOUTUBE_VIDEO, 'aFZy8iibMD0')
        media = Media.get_by_id(media_key)
        self.assertIsNotNone(media)
        self.assertEqual(media.media_type_enum, MediaType.YOUTUBE_VIDEO)
        self.assertEqual(media.foreign_key, 'aFZy8iibMD0')
        self.assertIn(ndb.Key(Event, '2014casj'), media.references)

    def test_update_event_info(self):
        self.event_info_auth.put()

        request = {
            'first_event_code': 'abc123',
            'playoff_type': PlayoffType.ROUND_ROBIN_6_TEAM,
            'webcasts': [{'url': 'https://youtu.be/abc123'},
                         {'type': 'youtube', 'channel': 'cde456'}],
            'remap_teams': {
                'frc9323': 'frc1323B',
                'frc9254': 'frc254B',
                'frc8254': 'frc254C',
                'frc9000': 'frc6000',
            },
            'someother': 'randomstuff',  # This should be ignored
        }
        request_body = json.dumps(request)
        request_path = '/api/trusted/v1/event/2014casj/info/update'
        sig = md5.new('{}{}{}'.format('321tEsTsEcReT', request_path, request_body)).hexdigest()
        response = self.testapp.post(request_path, request_body, headers={'X-TBA-Auth-Id': 'tEsT_id_9', 'X-TBA-Auth-Sig': sig})

        self.assertEqual(response.status_code, 200)

        event = Event.get_by_id('2014casj')
        self.assertEqual(event.first_code, 'abc123')
        self.assertEqual(event.official, True)
        self.assertEqual(event.playoff_type, PlayoffType.ROUND_ROBIN_6_TEAM)
        webcasts = event.webcast
        self.assertEqual(len(webcasts), 2)
        webcast = webcasts[0]
        self.assertEqual(webcast['type'], 'youtube')
        self.assertEqual(webcast['channel'], 'abc123')
        webcast = webcasts[1]
        self.assertEqual(webcast['type'], 'youtube')
        self.assertEqual(webcast['channel'], 'cde456')
        self.assertEqual(event.remap_teams, {
            'frc9323': 'frc1323B',
            'frc9254': 'frc254B',
            'frc8254': 'frc254C',
            'frc9000': 'frc6000',
        })

        # Test invalid remap_teams
        request = {
            'remap_teams': {
                'frc9323': 'frc1323b',  # lower case
            }
        }
        request_body = json.dumps(request)
        sig = md5.new('{}{}{}'.format('321tEsTsEcReT', request_path, request_body)).hexdigest()
        response = self.testapp.post(request_path, request_body, headers={'X-TBA-Auth-Id': 'tEsT_id_9', 'X-TBA-Auth-Sig': sig}, expect_errors=True)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(event.remap_teams, {
            'frc9323': 'frc1323B',
            'frc9254': 'frc254B',
            'frc8254': 'frc254C',
            'frc9000': 'frc6000',
        })

        request = {
            'remap_teams': {
                'frc9323': 'frc1323A',  # "A" team
            }
        }
        request_body = json.dumps(request)
        sig = md5.new('{}{}{}'.format('321tEsTsEcReT', request_path, request_body)).hexdigest()
        response = self.testapp.post(request_path, request_body, headers={'X-TBA-Auth-Id': 'tEsT_id_9', 'X-TBA-Auth-Sig': sig}, expect_errors=True)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(event.remap_teams, {
            'frc9323': 'frc1323B',
            'frc9254': 'frc254B',
            'frc8254': 'frc254C',
            'frc9000': 'frc6000',
        })

        request = {
            'remap_teams': {
                'frc9323': 'frc1323BB',  # Two letters
            }
        }
        request_body = json.dumps(request)
        sig = md5.new('{}{}{}'.format('321tEsTsEcReT', request_path, request_body)).hexdigest()
        response = self.testapp.post(request_path, request_body, headers={'X-TBA-Auth-Id': 'tEsT_id_9', 'X-TBA-Auth-Sig': sig}, expect_errors=True)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(event.remap_teams, {
            'frc9323': 'frc1323B',
            'frc9254': 'frc254B',
            'frc8254': 'frc254C',
            'frc9000': 'frc6000',
        })

        request = {
            'remap_teams': {
                'frc1323B': 'frc1323',  # Mapping from B team
            }
        }
        request_body = json.dumps(request)
        sig = md5.new('{}{}{}'.format('321tEsTsEcReT', request_path, request_body)).hexdigest()
        response = self.testapp.post(request_path, request_body, headers={'X-TBA-Auth-Id': 'tEsT_id_9', 'X-TBA-Auth-Sig': sig}, expect_errors=True)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(event.remap_teams, {
            'frc9323': 'frc1323B',
            'frc9254': 'frc254B',
            'frc8254': 'frc254C',
            'frc9000': 'frc6000',
        })

        request = {
            'remap_teams': {
                '1323': 'frc1323B',  # Bad starting format
            }
        }
        request_body = json.dumps(request)
        sig = md5.new('{}{}{}'.format('321tEsTsEcReT', request_path, request_body)).hexdigest()
        response = self.testapp.post(request_path, request_body, headers={'X-TBA-Auth-Id': 'tEsT_id_9', 'X-TBA-Auth-Sig': sig}, expect_errors=True)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(event.remap_teams, {
            'frc9323': 'frc1323B',
            'frc9254': 'frc254B',
            'frc8254': 'frc254C',
            'frc9000': 'frc6000',
        })

        request = {
            'remap_teams': {
                'frc1323': '1323B',  # Bad ending format
            }
        }
        request_body = json.dumps(request)
        sig = md5.new('{}{}{}'.format('321tEsTsEcReT', request_path, request_body)).hexdigest()
        response = self.testapp.post(request_path, request_body, headers={'X-TBA-Auth-Id': 'tEsT_id_9', 'X-TBA-Auth-Sig': sig}, expect_errors=True)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(event.remap_teams, {
            'frc9323': 'frc1323B',
            'frc9254': 'frc254B',
            'frc8254': 'frc254C',
            'frc9000': 'frc6000',
        })

    def test_remapping(self):
        self.event_info_auth.put()
        self.matches_auth.put()
        self.rankings_auth.put()
        self.alliances_auth.put()
        self.awards_auth.put()

        request = {
            'remap_teams': {
                'frc1': 'frc101B',
                'frc2': 'frc102B',
                'frc3': 'frc102C',
                'frc4': 'frc104'
            },
        }
        request_body = json.dumps(request)
        request_path = '/api/trusted/v1/event/2014casj/info/update'
        sig = md5.new('{}{}{}'.format('321tEsTsEcReT', request_path, request_body)).hexdigest()
        response = self.testapp.post(request_path, request_body, headers={'X-TBA-Auth-Id': 'tEsT_id_9', 'X-TBA-Auth-Sig': sig})
        self.assertEqual(response.status_code, 200)

        # Test remapped matches
        matches = [{
            'comp_level': 'f',
            'set_number': 1,
            'match_number': 2,
            'alliances': {
                'red': {'teams': ['frc1', 'frc2', 'frc3'],
                        'score': 250,
                        'surrogates': ['frc1'],
                        'dqs': ['frc1', 'frc2', 'frc3']},
                'blue': {'teams': ['frc4', 'frc5', 'frc6'],
                         'score': 260,
                         'surrogates': [],
                         'dqs': []},
            },
            'score_breakdown': {
                'red': {'auto': 20, 'assist': 40, 'truss+catch': 20, 'teleop_goal+foul': 20},
                'blue': {'auto': 40, 'assist': 60, 'truss+catch': 10, 'teleop_goal+foul': 40},
            },
            'time_string': '11:00 AM',
            'time_utc': '2014-08-31T18:00:00',
        }]
        request_body = json.dumps(matches)
        request_path = '/api/trusted/v1/event/2014casj/matches/update'
        sig = md5.new('{}{}{}'.format('321tEsTsEcReT', request_path, request_body)).hexdigest()
        response = self.testapp.post(request_path, request_body, headers={'X-TBA-Auth-Id': 'tEsT_id_1', 'X-TBA-Auth-Sig': sig}, expect_errors=True)
        self.assertEqual(response.status_code, 200)

        # verify remapped match data
        match = Match.get_by_id('2014casj_f1m2')
        self.assertEqual(match.time, datetime.datetime(2014, 8, 31, 18, 0))
        self.assertEqual(match.time_string, '11:00 AM')
        self.assertEqual(match.alliances['red']['teams'], ['frc101B', 'frc102B', 'frc102C'])
        self.assertEqual(match.alliances['red']['score'], 250)
        self.assertEqual(match.alliances['red']['surrogates'], ['frc101B'])
        self.assertEqual(match.alliances['red']['dqs'], ['frc101B', 'frc102B', 'frc102C'])
        self.assertEqual(match.score_breakdown['red']['truss+catch'], 20)
        self.assertEqual(match.alliances['blue']['teams'], ['frc104', 'frc5', 'frc6'])
        self.assertEqual(match.alliances['blue']['score'], 260)
        self.assertEqual(match.alliances['blue']['surrogates'], [])
        self.assertEqual(match.alliances['blue']['dqs'], [])
        self.assertEqual(set(match.team_key_names), set(['frc101B', 'frc102B', 'frc102C', 'frc104', 'frc5', 'frc6']))

        # Test remapped alliances
        alliances = [['frc1', 'frc2', 'frc3'],
                     ['frc4', 'frc5', 'frc6'],
                     ['frc7', 'frc8', 'frc9']]
        request_body = json.dumps(alliances)

        request_path = '/api/trusted/v1/event/2014casj/alliance_selections/update'
        sig = md5.new('{}{}{}'.format('321tEsTsEcReT', request_path, request_body)).hexdigest()
        response = self.testapp.post(request_path, request_body, headers={'X-TBA-Auth-Id': 'tEsT_id_3', 'X-TBA-Auth-Sig': sig}, expect_errors=True)
        self.assertEqual(response.status_code, 200)

        # Test remapped rankings
        rankings = {
            'breakdowns': ['QS', 'Auton', 'Teleop', 'T&C', 'wins', 'losses', 'ties'],
            'rankings': [
                {'team_key': 'frc1', 'rank': 1, 'wins': 10, 'losses': 0, 'ties': 0, 'played': 10, 'dqs': 0, 'QS': 20, 'Auton': 500, 'Teleop': 500, 'T&C': 200},
                {'team_key': 'frc2', 'rank': 2, 'wins': 10, 'losses': 0, 'ties': 0, 'played': 10, 'dqs': 0, 'QS': 20, 'Auton': 500, 'Teleop': 500, 'T&C': 200},
                {'team_key': 'frc3', 'rank': 3, 'wins': 10, 'losses': 0, 'ties': 0, 'played': 10, 'dqs': 0, 'QS': 20, 'Auton': 500, 'Teleop': 500, 'T&C': 200},
                {'team_key': 'frc4', 'rank': 4, 'wins': 10, 'losses': 0, 'ties': 0, 'played': 10, 'dqs': 0, 'QS': 20, 'Auton': 500, 'Teleop': 500, 'T&C': 200},
                {'team_key': 'frc5', 'rank': 5, 'wins': 10, 'losses': 0, 'ties': 0, 'played': 10, 'dqs': 0, 'QS': 20, 'Auton': 500, 'Teleop': 500, 'T&C': 200},
                {'team_key': 'frc6', 'rank': 6, 'wins': 10, 'losses': 0, 'ties': 0, 'played': 10, 'dqs': 0, 'QS': 20, 'Auton': 500, 'Teleop': 500, 'T&C': 200},
            ],
        }
        request_body = json.dumps(rankings)

        request_path = '/api/trusted/v1/event/2014casj/rankings/update'
        sig = md5.new('{}{}{}'.format('321tEsTsEcReT', request_path, request_body)).hexdigest()
        response = self.testapp.post(request_path, request_body, headers={'X-TBA-Auth-Id': 'tEsT_id_2', 'X-TBA-Auth-Sig': sig}, expect_errors=True)
        self.assertEqual(response.status_code, 200)

        # verify remapped alliances
        self.assertEqual(len(self.event.alliance_selections), 3)
        self.assertEqual(self.event.alliance_selections[0]['picks'], ['frc101B', 'frc102B', 'frc102C'])
        self.assertEqual(self.event.alliance_selections[1]['picks'], ['frc104', 'frc5', 'frc6'])
        self.assertEqual(self.event.alliance_selections[2]['picks'], ['frc7', 'frc8', 'frc9'])

        # verify remapped rankings
        self.assertEqual(self.event.rankings[0], ['Rank', 'Team', 'QS', 'Auton', 'Teleop', 'T&C', 'Record (W-L-T)', 'DQ', 'Played'])
        self.assertEqual(self.event.rankings[1], [1, '101B', 20, 500, 500, 200, '10-0-0', 0, 10])
        self.assertEqual(self.event.rankings[2], [2, '102B', 20, 500, 500, 200, '10-0-0', 0, 10])
        self.assertEqual(self.event.rankings[3], [3, '102C', 20, 500, 500, 200, '10-0-0', 0, 10])
        self.assertEqual(self.event.rankings[4], [4, '104', 20, 500, 500, 200, '10-0-0', 0, 10])
        self.assertEqual(self.event.rankings[5], [5, '5', 20, 500, 500, 200, '10-0-0', 0, 10])
        self.assertEqual(self.event.rankings[6], [6, '6', 20, 500, 500, 200, '10-0-0', 0, 10])

        # Test remapped awards
        awards = [{'name_str': 'Winner', 'team_key': 'frc1'},
                  {'name_str': 'Winner', 'team_key': 'frc2'},
                  {'name_str': 'Winner', 'team_key': 'frc3'},
                  {'name_str': 'Volunteer Blahblah', 'team_key': 'frc4', 'awardee': 'Bob Bobby'},
                  {'name_str': 'Chairman\'s Blahblah', 'team_key': 'frc5'},
                  {'name_str': 'Finalist', 'team_key': 'frc6'}]
        request_body = json.dumps(awards)

        request_path = '/api/trusted/v1/event/2014casj/awards/update'
        sig = md5.new('{}{}{}'.format('321tEsTsEcReT', request_path, request_body)).hexdigest()
        response = self.testapp.post(request_path, request_body, headers={'X-TBA-Auth-Id': 'tEsT_id_4', 'X-TBA-Auth-Sig': sig}, expect_errors=True)
        self.assertEqual(response.status_code, 200)

        for team in Award.get_by_id('2014casj_1').recipient_dict.keys():
            self.assertTrue(str(team) in {'101B', '102B', '102C'})
        for team in Award.get_by_id('2014casj_5').recipient_dict.keys():
            self.assertTrue(str(team) in {'104'})
        for team in Award.get_by_id('2014casj_0').recipient_dict.keys():
            self.assertTrue(str(team) in {'5'})
        for team in Award.get_by_id('2014casj_2').recipient_dict.keys():
            self.assertTrue(str(team) in {'6'})

    def test_remapping_after(self):
        self.event_info_auth.put()
        self.matches_auth.put()
        self.rankings_auth.put()
        self.alliances_auth.put()
        self.awards_auth.put()

        # Test remapped matches
        matches = [{
            'comp_level': 'f',
            'set_number': 1,
            'match_number': 2,
            'alliances': {
                'red': {'teams': ['frc1', 'frc2', 'frc3'],
                        'score': 250,
                        'surrogates': ['frc1'],
                        'dqs': ['frc1', 'frc2', 'frc3']},
                'blue': {'teams': ['frc4', 'frc5', 'frc6'],
                         'score': 260,
                         'surrogates': [],
                         'dqs': []},
            },
            'score_breakdown': {
                'red': {'auto': 20, 'assist': 40, 'truss+catch': 20, 'teleop_goal+foul': 20},
                'blue': {'auto': 40, 'assist': 60, 'truss+catch': 10, 'teleop_goal+foul': 40},
            },
            'time_string': '11:00 AM',
            'time_utc': '2014-08-31T18:00:00',
        }]
        request_body = json.dumps(matches)
        request_path = '/api/trusted/v1/event/2014casj/matches/update'
        sig = md5.new('{}{}{}'.format('321tEsTsEcReT', request_path, request_body)).hexdigest()
        response = self.testapp.post(request_path, request_body, headers={'X-TBA-Auth-Id': 'tEsT_id_1', 'X-TBA-Auth-Sig': sig}, expect_errors=True)
        self.assertEqual(response.status_code, 200)

        # Test remapped alliances
        alliances = [['frc1', 'frc2', 'frc3'],
                     ['frc4', 'frc5', 'frc6'],
                     ['frc7', 'frc8', 'frc9']]
        request_body = json.dumps(alliances)

        request_path = '/api/trusted/v1/event/2014casj/alliance_selections/update'
        sig = md5.new('{}{}{}'.format('321tEsTsEcReT', request_path, request_body)).hexdigest()
        response = self.testapp.post(request_path, request_body, headers={'X-TBA-Auth-Id': 'tEsT_id_3', 'X-TBA-Auth-Sig': sig}, expect_errors=True)
        self.assertEqual(response.status_code, 200)

        # Test remapped rankings
        rankings = {
            'breakdowns': ['QS', 'Auton', 'Teleop', 'T&C', 'wins', 'losses', 'ties'],
            'rankings': [
                {'team_key': 'frc1', 'rank': 1, 'wins': 10, 'losses': 0, 'ties': 0, 'played': 10, 'dqs': 0, 'QS': 20, 'Auton': 500, 'Teleop': 500, 'T&C': 200},
                {'team_key': 'frc2', 'rank': 2, 'wins': 10, 'losses': 0, 'ties': 0, 'played': 10, 'dqs': 0, 'QS': 20, 'Auton': 500, 'Teleop': 500, 'T&C': 200},
                {'team_key': 'frc3', 'rank': 3, 'wins': 10, 'losses': 0, 'ties': 0, 'played': 10, 'dqs': 0, 'QS': 20, 'Auton': 500, 'Teleop': 500, 'T&C': 200},
                {'team_key': 'frc4', 'rank': 4, 'wins': 10, 'losses': 0, 'ties': 0, 'played': 10, 'dqs': 0, 'QS': 20, 'Auton': 500, 'Teleop': 500, 'T&C': 200},
                {'team_key': 'frc5', 'rank': 5, 'wins': 10, 'losses': 0, 'ties': 0, 'played': 10, 'dqs': 0, 'QS': 20, 'Auton': 500, 'Teleop': 500, 'T&C': 200},
                {'team_key': 'frc6', 'rank': 6, 'wins': 10, 'losses': 0, 'ties': 0, 'played': 10, 'dqs': 0, 'QS': 20, 'Auton': 500, 'Teleop': 500, 'T&C': 200},
            ],
        }
        request_body = json.dumps(rankings)

        request_path = '/api/trusted/v1/event/2014casj/rankings/update'
        sig = md5.new('{}{}{}'.format('321tEsTsEcReT', request_path, request_body)).hexdigest()
        response = self.testapp.post(request_path, request_body, headers={'X-TBA-Auth-Id': 'tEsT_id_2', 'X-TBA-Auth-Sig': sig}, expect_errors=True)
        self.assertEqual(response.status_code, 200)

        # Test remapped awards
        awards = [{'name_str': 'Winner', 'team_key': 'frc1'},
                  {'name_str': 'Winner', 'team_key': 'frc2'},
                  {'name_str': 'Winner', 'team_key': 'frc3'},
                  {'name_str': 'Volunteer Blahblah', 'team_key': 'frc4', 'awardee': 'Bob Bobby'},
                  {'name_str': 'Chairman\'s Blahblah', 'team_key': 'frc5'},
                  {'name_str': 'Finalist', 'team_key': 'frc6'}]
        request_body = json.dumps(awards)

        request_path = '/api/trusted/v1/event/2014casj/awards/update'
        sig = md5.new('{}{}{}'.format('321tEsTsEcReT', request_path, request_body)).hexdigest()
        response = self.testapp.post(request_path, request_body, headers={'X-TBA-Auth-Id': 'tEsT_id_4', 'X-TBA-Auth-Sig': sig}, expect_errors=True)
        self.assertEqual(response.status_code, 200)

        # Set remapping
        request = {
            'remap_teams': {
                'frc1': 'frc101B',
                'frc2': 'frc102B',
                'frc3': 'frc102C',
                'frc4': 'frc104'
            },
        }
        request_body = json.dumps(request)
        request_path = '/api/trusted/v1/event/2014casj/info/update'
        sig = md5.new('{}{}{}'.format('321tEsTsEcReT', request_path, request_body)).hexdigest()
        response = self.testapp.post(request_path, request_body, headers={'X-TBA-Auth-Id': 'tEsT_id_9', 'X-TBA-Auth-Sig': sig})
        self.assertEqual(response.status_code, 200)

        # Run tasks
        tasks = self.taskqueue_stub.GetTasks('admin')
        for task in tasks:
            self.cronapp.get(task["url"])

        # verify remapped match data
        match = Match.get_by_id('2014casj_f1m2')
        self.assertEqual(match.time, datetime.datetime(2014, 8, 31, 18, 0))
        self.assertEqual(match.time_string, '11:00 AM')
        self.assertEqual(match.alliances['red']['teams'], ['frc101B', 'frc102B', 'frc102C'])
        self.assertEqual(match.alliances['red']['score'], 250)
        self.assertEqual(match.alliances['red']['surrogates'], ['frc101B'])
        self.assertEqual(match.alliances['red']['dqs'], ['frc101B', 'frc102B', 'frc102C'])
        self.assertEqual(match.score_breakdown['red']['truss+catch'], 20)
        self.assertEqual(match.alliances['blue']['teams'], ['frc104', 'frc5', 'frc6'])
        self.assertEqual(match.alliances['blue']['score'], 260)
        self.assertEqual(match.alliances['blue']['surrogates'], [])
        self.assertEqual(match.alliances['blue']['dqs'], [])
        self.assertEqual(set(match.team_key_names), set(['frc101B', 'frc102B', 'frc102C', 'frc104', 'frc5', 'frc6']))

        # verify remapped alliances
        self.assertEqual(len(self.event.alliance_selections), 3)
        self.assertEqual(self.event.alliance_selections[0]['picks'], ['frc101B', 'frc102B', 'frc102C'])
        self.assertEqual(self.event.alliance_selections[1]['picks'], ['frc104', 'frc5', 'frc6'])
        self.assertEqual(self.event.alliance_selections[2]['picks'], ['frc7', 'frc8', 'frc9'])

        # verify remapped rankings
        self.assertEqual(self.event.rankings[0], ['Rank', 'Team', 'QS', 'Auton', 'Teleop', 'T&C', 'Record (W-L-T)', 'DQ', 'Played'])
        self.assertEqual(self.event.rankings[1], [1, '101B', 20, 500, 500, 200, '10-0-0', 0, 10])
        self.assertEqual(self.event.rankings[2], [2, '102B', 20, 500, 500, 200, '10-0-0', 0, 10])
        self.assertEqual(self.event.rankings[3], [3, '102C', 20, 500, 500, 200, '10-0-0', 0, 10])
        self.assertEqual(self.event.rankings[4], [4, '104', 20, 500, 500, 200, '10-0-0', 0, 10])
        self.assertEqual(self.event.rankings[5], [5, '5', 20, 500, 500, 200, '10-0-0', 0, 10])
        self.assertEqual(self.event.rankings[6], [6, '6', 20, 500, 500, 200, '10-0-0', 0, 10])

        # verify remapped awards
        for team in Award.get_by_id('2014casj_1').recipient_dict.keys():
            self.assertTrue(str(team) in {'101B', '102B', '102C'})
        for team in Award.get_by_id('2014casj_5').recipient_dict.keys():
            self.assertTrue(str(team) in {'104'})
        for team in Award.get_by_id('2014casj_0').recipient_dict.keys():
            self.assertTrue(str(team) in {'5'})
        for team in Award.get_by_id('2014casj_2').recipient_dict.keys():
            self.assertTrue(str(team) in {'6'})

    def test_zebra_motionworks_add(self):
        self.event_zebra_motionworks.put()
        match1 = Match(
            id="2014casj_qm1",
            alliances_json="""{"blue": {"score": -1, "teams": ["frc1", "frc2", "frc3"]}, "red": {"score": -1, "teams": ["frc254", "frc971", "frc604"]}}""",
            comp_level="qm",
            event=ndb.Key(Event, '2014casj'),
            year=2014,
            set_number=1,
            match_number=1,
            team_key_names=[u'frc254', u'frc971', u'frc604', u'frc1', u'frc2', u'frc3'],
            youtube_videos=["abcdef"]
        )

        data = [{
            "key": "2014casj_qm1",
            "times": [0.0, 0.5, 1.0, 1.5],
            "alliances": {
                "red": [
                    {
                        "team_key": "frc254",
                        "xs": [None, 1.2, 1.3, 1.4],
                        "ys": [None, 0.1, 0.1, 0.1],
                    },
                    {
                        "team_key": "frc971",
                        "xs": [1.1, 1.2, 1.3, 1.4],
                        "ys": [0.1, 0.1, 0.1, 0.1],
                    },
                    {
                        "team_key": "frc604",
                        "xs": [1.1, 1.2, 1.3, 1.4],
                        "ys": [0.1, 0.1, 0.1, 0.1],
                    },
                ],
                "blue": [
                    {
                        "team_key": "frc1",
                        "xs": [None, 1.2, 1.3, 1.4],
                        "ys": [None, 0.1, 0.1, 0.1],
                    },
                    {
                        "team_key": "frc2",
                        "xs": [1.1, 1.2, 1.3, 1.4],
                        "ys": [0.1, 0.1, 0.1, 0.1],
                    },
                    {
                        "team_key": "frc3",
                        "xs": [1.1, 1.2, None, 1.4],
                        "ys": [0.1, 0.1, None, 0.1],
                    },
                ],
            }
        }]

        # Verify failure if Match doesn't exist
        request_body = json.dumps(data)
        request_path = '/api/trusted/v1/event/2014casj/zebra_motionworks/add'
        sig = md5.new('{}{}{}'.format('321tEsTsEcReT', request_path, request_body)).hexdigest()
        response = self.testapp.post(request_path, request_body, headers={'X-TBA-Auth-Id': 'tEsT_id_10', 'X-TBA-Auth-Sig': sig}, expect_errors=True)

        self.assertEqual(response.status_code, 400)
        self.assertIsNone(ZebraMotionWorks.get_by_id('2014casj_qm1'))

        # Add match
        match1.put()

        # Verify bad event_key doesn't get added
        bad_data = copy.deepcopy(data)
        bad_data[0]['key'] = '2019casj_qm1'
        request_body = json.dumps(bad_data)
        request_path = '/api/trusted/v1/event/2014casj/zebra_motionworks/add'
        sig = md5.new('{}{}{}'.format('321tEsTsEcReT', request_path, request_body)).hexdigest()
        response = self.testapp.post(request_path, request_body, headers={'X-TBA-Auth-Id': 'tEsT_id_10', 'X-TBA-Auth-Sig': sig}, expect_errors=True)

        self.assertEqual(response.status_code, 400)
        self.assertIsNone(ZebraMotionWorks.get_by_id('2014casj_qm1'))

        # Verify malformatted data doesn't get added
        bad_data = copy.deepcopy(data)
        del bad_data[0]['times'][0]
        request_body = json.dumps(bad_data)
        request_path = '/api/trusted/v1/event/2014casj/zebra_motionworks/add'
        sig = md5.new('{}{}{}'.format('321tEsTsEcReT', request_path, request_body)).hexdigest()
        response = self.testapp.post(request_path, request_body, headers={'X-TBA-Auth-Id': 'tEsT_id_10', 'X-TBA-Auth-Sig': sig}, expect_errors=True)

        self.assertEqual(response.status_code, 400)
        self.assertIsNone(ZebraMotionWorks.get_by_id('2014casj_qm1'))

        # Verify teams must be the same
        bad_data = copy.deepcopy(data)
        bad_data[0]['alliances']['red'][0]['team_key'] = 'frc9999'
        request_body = json.dumps(bad_data)
        request_path = '/api/trusted/v1/event/2014casj/zebra_motionworks/add'
        sig = md5.new('{}{}{}'.format('321tEsTsEcReT', request_path, request_body)).hexdigest()
        response = self.testapp.post(request_path, request_body, headers={'X-TBA-Auth-Id': 'tEsT_id_10', 'X-TBA-Auth-Sig': sig}, expect_errors=True)

        self.assertEqual(response.status_code, 400)
        self.assertIsNone(ZebraMotionWorks.get_by_id('2014casj_qm1'))

        # Verify correctly added data
        request_body = json.dumps(data)
        request_path = '/api/trusted/v1/event/2014casj/zebra_motionworks/add'
        sig = md5.new('{}{}{}'.format('321tEsTsEcReT', request_path, request_body)).hexdigest()
        response = self.testapp.post(request_path, request_body, headers={'X-TBA-Auth-Id': 'tEsT_id_10', 'X-TBA-Auth-Sig': sig}, expect_errors=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(ZebraMotionWorks.get_by_id('2014casj_qm1').data, data[0])
