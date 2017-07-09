import unittest2
import webapp2
import webtest
from datetime import datetime

from google.appengine.ext import ndb
from google.appengine.ext import testbed
from webapp2_extras.routes import RedirectRoute

from consts.district_type import DistrictType
from consts.event_type import EventType
from controllers.suggestions.suggest_event_webcast_controller import SuggestEventWebcastController
from models.account import Account
from models.event import Event
from models.suggestion import Suggestion


class TestSuggestEventWebcastController(unittest2.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_user_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        app = webapp2.WSGIApplication([
            RedirectRoute(r'/suggest/event/webcast', SuggestEventWebcastController, 'suggest-webcast', strict_slash=True),
        ], debug=True)
        self.testapp = webtest.TestApp(app)

        self.event = Event(
            id="2016necmp",
            name="New England District Championship",
            event_type_enum=EventType.DISTRICT_CMP,
            event_district_enum=DistrictType.NEW_ENGLAND,
            short_name="New England",
            event_short="necmp",
            year=2016,
            end_date=datetime(2016, 03, 27),
            official=False,
            city='Hartford',
            state_prov='CT',
            country='USA',
            venue="Some Venue",
            venue_address="Some Venue, Hartford, CT, USA",
            timezone_id="America/New_York",
            start_date=datetime(2016, 03, 24),
            webcast_json="",
            website="http://www.firstsv.org"
        )
        self.event.put()

    def tearDown(self):
        self.testbed.deactivate()

    def loginUser(self):
        self.testbed.setup_env(
            user_email="user@example.com",
            user_id="123",
            user_is_admin='0',
            overwrite=True
        )

        Account.get_or_insert(
            "123",
            email="user@example.com",
            registered=True
        )

    def getSuggestionForm(self, event_key):
        response = self.testapp.get('/suggest/event/webcast?event_key={}'.format(event_key))
        self.assertEqual(response.status_int, 200)

        form = response.forms.get('suggest_webcast', None)
        self.assertIsNotNone(form)
        return form

    def test_login_redirect(self):
        response = self.testapp.get('/suggest/event/webcast?event_key=2016necmp', status='3*')
        response = response.follow(expect_errors=True)
        self.assertTrue(response.request.path.startswith("/account/login_required"))

    def test_no_params(self):
        self.loginUser()
        response = self.testapp.get('/suggest/event/webcast', status='3*')
        response = response.follow(expect_errors=True)
        self.assertEqual(response.request.path, '/')

    def test_submit_empty_form(self):
        self.loginUser()
        form = self.getSuggestionForm('2016necmp')
        response = form.submit().follow()
        self.assertEqual(response.status_int, 200)

        request = response.request
        self.assertEqual(request.GET.get('status'), 'blank_webcast')

    def test_submit_bad_url(self):
        self.loginUser()
        form = self.getSuggestionForm('2016necmp')
        form['webcast_url'] = 'The Blue Alliance'
        response = form.submit().follow()
        self.assertEqual(response.status_int, 200)

        request = response.request
        self.assertEqual(request.GET.get('status'), 'invalid_url')

    def test_submit_tba_url(self):
        self.loginUser()
        form = self.getSuggestionForm('2016necmp')
        form['webcast_url'] = 'http://thebluealliance.com'
        response = form.submit().follow()
        self.assertEqual(response.status_int, 200)

        request = response.request
        self.assertEqual(request.GET.get('status'), 'invalid_url')

    def test_submit_webcast(self):
        self.loginUser()
        form = self.getSuggestionForm('2016necmp')
        form['webcast_url'] = 'https://twitch.tv/frcgamesense'
        response = form.submit().follow()
        self.assertEqual(response.status_int, 200)

        request = response.request
        self.assertEqual(request.GET.get('status'), 'success')

        # Make sure the Suggestion gets created
        suggestion = Suggestion.query().fetch()[0]
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion.review_state, Suggestion.REVIEW_PENDING)
        self.assertEqual(suggestion.target_key, '2016necmp')
        self.assertEqual(suggestion.contents['webcast_url'], 'https://twitch.tv/frcgamesense')
        self.assertIsNotNone(suggestion.contents.get('webcast_dict'))
