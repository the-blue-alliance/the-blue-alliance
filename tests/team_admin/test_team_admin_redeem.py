import datetime
import unittest2
import webapp2
import webtest

from google.appengine.datastore import datastore_stub_util
from google.appengine.ext import ndb
from google.appengine.ext import testbed
from webapp2_extras.routes import RedirectRoute

from controllers.team_admin_controller import TeamAdminRedeem
from models.account import Account
from models.team import Team
from models.team_admin_access import TeamAdminAccess


class TestTeamAdminRedeem(unittest2.TestCase):
    def setUp(self):
        self.policy = datastore_stub_util.PseudoRandomHRConsistencyPolicy(
            probability=1)
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub(consistency_policy=self.policy)
        self.testbed.init_memcache_stub()
        self.testbed.init_user_stub()
        self.testbed.init_urlfetch_stub()
        self.testbed.init_taskqueue_stub(_all_queues_valid=True)
        ndb.get_context().clear_cache(
        )  # Prevent data from leaking between tests

        app = webapp2.WSGIApplication([
            RedirectRoute(
                r'/mod/redeem',
                TeamAdminRedeem,
                'team-admin',
                strict_slash=True),
        ])
        self.testapp = webtest.TestApp(app)

        self.team = Team(
            id="frc1124",
            name="Team",
            team_number=1124,
        )
        self.team.put()
        self.now = datetime.datetime.now()

    def tearDown(self):
        self.testbed.deactivate()

    def loginUser(self):
        self.testbed.setup_env(
            user_email="user@example.com",
            user_id="123",
            user_is_admin='0',
            overwrite=True)

        self.account = Account.get_or_insert(
            "123", email="user@example.com", registered=True)

    def addTeamAdminAccess(self, account, team_number=1124):
        access = TeamAdminAccess(
            id="test_access",
            access_code="abc123",
            team_number=team_number,
            year=self.now.year,
            expiration=self.now + datetime.timedelta(days=1),
            account=account,
        )
        return access.put()

    def getForm(self):
        response = self.testapp.get('/mod/redeem')
        self.assertEqual(response.status_int, 200)

        form = response.forms.get('redeem', None)
        self.assertIsNotNone(form)
        return form

    def test_login_redirect(self):
        response = self.testapp.get('/mod/redeem', status='3*')
        response = response.follow(expect_errors=True)
        self.assertTrue(
            response.request.path.startswith("/account/login_required"))

    def test_cant_redeem_with_code_linked(self):
        self.loginUser()
        access_key = self.addTeamAdminAccess(account=self.account.key)
        response = self.testapp.get('/mod/redeem')
        self.assertEqual(response.status_int, 200)

        # If there's an existing code linked, the form shouldn't render
        form = response.forms.get('redeem', None)
        self.assertIsNone(form)

    def test_redeem_bad_code(self):
        self.loginUser()

        form = self.getForm()
        form['auth_code'] = 'abc123'
        response = form.submit().follow()

        self.assertEqual(response.request.GET['status'], 'invalid_code')

    def test_redeem_code(self):
        self.loginUser()
        access_key = self.addTeamAdminAccess(account=None)

        form = self.getForm()
        form['auth_code'] = 'abc123'
        response = form.submit().follow()

        access = access_key.get()
        self.assertEqual(response.request.GET['status'], 'success')
        self.assertEqual(self.account.key, access.account)

    def test_redeem_used_code(self):
        self.loginUser()
        access_key = self.addTeamAdminAccess(
            account=ndb.Key(Account, 'other-user@example.com'))

        form = self.getForm()
        form['auth_code'] = 'abc123'
        response = form.submit().follow()

        self.assertEqual(response.request.GET['status'], 'code_used')

    def test_redeem_code_existing_link(self):
        self.loginUser()
        access_key = self.addTeamAdminAccess(account=None)

        form = self.getForm()
        form['auth_code'] = 'abc123'

        access = access_key.get()
        access.account = self.account.key
        access.put()

        response = form.submit().follow()

        self.assertEqual(response.request.GET['status'], 'already_linked')
