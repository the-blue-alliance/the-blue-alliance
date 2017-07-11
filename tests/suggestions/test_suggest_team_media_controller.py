import unittest2
import webapp2
import webtest

from google.appengine.ext import ndb
from google.appengine.ext import testbed
from webapp2_extras.routes import RedirectRoute

from controllers.suggestions.suggest_team_media_controller import SuggestTeamMediaController, \
    SuggestTeamSocialMediaController
from models.account import Account
from models.suggestion import Suggestion
from models.team import Team


class TestSuggestTeamMediaController(unittest2.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_user_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        app = webapp2.WSGIApplication([
            RedirectRoute(r'/suggest/team/media', SuggestTeamMediaController, 'suggest-team-media', strict_slash=True),
        ], debug=True)
        self.testapp = webtest.TestApp(app)

    def tearDown(self):
        self.testbed.deactivate()

    def loginUser(self):
        self.testbed.setup_env(
            user_email="user@example.com",
            user_id="123",
            user_is_admin='0',
            overwrite=True)

        Account.get_or_insert(
            "123",
            email="user@example.com",
            registered=True)

    def storeTeam(self):
        self.team = Team(
            id="frc1124",
            team_number=1124,
        )
        self.team.put()

    def getSuggestionForm(self, team_key, year):
        response = self.testapp.get('/suggest/team/media?team_key={}&year={}'.format(team_key, year))
        self.assertEqual(response.status_int, 200)

        form = response.forms.get('suggest_media', None)
        self.assertIsNotNone(form)
        return form

    def test_login_redirect(self):
        response = self.testapp.get('/suggest/team/media?team_key=frc1124&year=2016', status='3*')
        response = response.follow(expect_errors=True)
        self.assertTrue(response.request.path.startswith("/account/login_required"))

    def test_no_params(self):
        self.loginUser()
        response = self.testapp.get('/suggest/team/media', status='3*')
        response = response.follow(expect_errors=True)
        self.assertEqual(response.request.path, '/')

    def test_submit_empty_form(self):
        self.loginUser()
        self.storeTeam()
        form = self.getSuggestionForm('frc1124', 2016)
        response = form.submit().follow()
        self.assertEqual(response.status_int, 200)

        request = response.request
        self.assertEqual(request.GET.get('status'), 'bad_url')

    def test_bad_team(self):
        self.loginUser()
        response = self.testapp.get('/suggest/team/media?team_key=frc1124&year=2016', status='3*')
        response = response.follow(expect_errors=True)
        self.assertEqual(response.request.path, '/')

    def test_suggest_media(self):
        self.loginUser()
        self.storeTeam()
        form = self.getSuggestionForm('frc1124', 2016)
        form['media_url'] = 'http://imgur.com/aF8T5ZE'
        response = form.submit().follow()
        self.assertEqual(response.status_int, 200)

        request = response.request
        self.assertEqual(request.GET.get('status'), 'success')

        suggestion = Suggestion.get_by_id('media_2016_team_frc1124_imgur_aF8T5ZE')
        self.assertIsNotNone(suggestion)


class TestSuggestTeamSocialMediaController(unittest2.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_user_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        app = webapp2.WSGIApplication([
            RedirectRoute(r'/suggest/team/social_media', SuggestTeamSocialMediaController, 'suggest-team-social-media', strict_slash=True),
        ], debug=True)
        self.testapp = webtest.TestApp(app)

    def tearDown(self):
        self.testbed.deactivate()

    def loginUser(self):
        self.testbed.setup_env(
            user_email="user@example.com",
            user_id="123",
            user_is_admin='0',
            overwrite=True)

        Account.get_or_insert(
            "123",
            email="user@example.com",
            registered=True)

    def storeTeam(self):
        self.team = Team(
            id="frc1124",
            team_number=1124,
        )
        self.team.put()

    def getSuggestionForm(self, team_key):
        response = self.testapp.get('/suggest/team/social_media?team_key={}'.format(team_key))
        self.assertEqual(response.status_int, 200)

        form = response.forms.get('suggest_social_media', None)
        self.assertIsNotNone(form)
        return form

    def test_login_redirect(self):
        response = self.testapp.get('/suggest/team/social_media?team_key=frc1124', status='3*')
        response = response.follow(expect_errors=True)
        self.assertTrue(response.request.path.startswith("/account/login_required"))

    def test_no_params(self):
        self.loginUser()
        response = self.testapp.get('/suggest/team/social_media', status='3*')
        response = response.follow(expect_errors=True)
        self.assertEqual(response.request.path, '/')

    def test_submit_empty_form(self):
        self.loginUser()
        self.storeTeam()
        form = self.getSuggestionForm('frc1124')
        response = form.submit().follow()
        self.assertEqual(response.status_int, 200)

        request = response.request
        self.assertEqual(request.GET.get('status'), 'bad_url')

    def test_bad_team(self):
        self.loginUser()
        response = self.testapp.get('/suggest/team/social_media?team_key=frc1124', status='3*')
        response = response.follow(expect_errors=True)
        self.assertEqual(response.request.path, '/')

    def test_suggest_team(self):
        self.loginUser()
        self.storeTeam()
        form = self.getSuggestionForm('frc1124')
        form['media_url'] = 'https://github.com/frc1124'
        response = form.submit().follow()
        self.assertEqual(response.status_int, 200)

        request = response.request
        self.assertEqual(request.GET.get('status'), 'success')

        suggestion = Suggestion.get_by_id('media_None_team_frc1124_github-profile_frc1124')
        self.assertIsNotNone(suggestion)
