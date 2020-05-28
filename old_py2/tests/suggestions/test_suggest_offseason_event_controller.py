import unittest2
import webapp2
import webtest

from google.appengine.ext import ndb
from google.appengine.ext import testbed
from webapp2_extras.routes import RedirectRoute

from controllers.suggestions.suggest_offseason_event_controller import \
    SuggestOffseasonEventController
from models.account import Account


class TestSuggestOffseasonEventController(unittest2.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_user_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        app = webapp2.WSGIApplication([
            RedirectRoute(r'/suggest/offseason', SuggestOffseasonEventController, 'request-apiwrite', strict_slash=True),
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

    def getSuggestionForm(self):
        response = self.testapp.get('/suggest/offseason')
        self.assertEqual(response.status_int, 200)

        form = response.forms.get('suggest_offseason', None)
        self.assertIsNotNone(form)
        return form

    def test_login_redirect(self):
        response = self.testapp.get('/suggest/offseason', status='3*')
        response = response.follow(expect_errors=True)
        self.assertTrue(response.request.path.startswith("/account/login_required"))

    def test_submit_empty_form(self):
        self.loginUser()
        form = self.getSuggestionForm()
        response = form.submit()
        self.assertEqual(response.status_int, 200)

    def test_suggest_event(self):
        self.loginUser()
        form = self.getSuggestionForm()
        form['name'] = 'Test Event'
        form['start_date'] = '2012-04-04'
        form['end_date'] = '2012-04-06'
        form['website'] = 'http://foo.com/bar'
        form['venue_name'] = 'This is a Venue'
        form['venue_address'] = '123 Fake St'
        form['venue_city'] = 'New York'
        form['venue_state'] = 'NY'
        form['venue_country'] = "USA"
        response = form.submit().follow()
        self.assertEqual(response.status_int, 200)
