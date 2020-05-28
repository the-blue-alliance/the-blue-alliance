import unittest2
import webapp2
import webtest
from datetime import datetime

from google.appengine.ext import testbed
from google.appengine.ext import ndb
from webapp2_extras.routes import RedirectRoute

from consts.auth_type import AuthType
from consts.district_type import DistrictType
from consts.event_type import EventType
from controllers.suggestions.suggest_apiwrite_controller import SuggestApiWriteController
from models.account import Account
from models.event import Event
from models.suggestion import Suggestion


class TestSuggestApiWriteController(unittest2.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_user_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        app = webapp2.WSGIApplication([
            RedirectRoute(r'/request/apiwrite', SuggestApiWriteController, 'request-apiwrite', strict_slash=True),
        ], debug=True)
        self.testapp = webtest.TestApp(app)

        self.event = Event(
            id="2016necmp",
            name="New England District Championship",
            event_type_enum=EventType.OFFSEASON,
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
            webcast_json="[{\"type\": \"twitch\", \"channel\": \"frcgamesense\"}]",
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

    def getSuggestionForm(self):
        response = self.testapp.get('/request/apiwrite')
        self.assertEqual(response.status_int, 200)

        form = response.forms.get('suggest_apiwrite', None)
        self.assertIsNotNone(form)
        return form

    def test_login_redirect(self):
        response = self.testapp.get('/request/apiwrite', status='3*')
        response = response.follow(expect_errors=True)
        self.assertTrue(response.request.path.startswith("/account/login_required"))

    def test_submit_empty_form(self):
        self.loginUser()
        form = self.getSuggestionForm()
        response = form.submit().follow()
        self.assertEqual(response.status_int, 200)

        # We should throw an error becase no affiliation was set
        request = response.request
        self.assertEqual(request.GET.get('status'), 'no_affiliation')

    def test_suggest_api_write(self):
        self.loginUser()
        form = self.getSuggestionForm()
        form['event_key'] = '2016necmp'
        form['role'] = 'Test Code'
        form.get('auth_types', index=0).checked = True
        form.get('auth_types', index=1).checked = True
        response = form.submit().follow()
        self.assertEqual(response.status_int, 200)

        # Make sure the Suggestion gets created
        suggestion = Suggestion.query().fetch()[0]
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion.review_state, Suggestion.REVIEW_PENDING)
        self.assertEqual(suggestion.contents['event_key'], '2016necmp')
        self.assertEqual(suggestion.contents['affiliation'], 'Test Code')
        self.assertListEqual(suggestion.contents['auth_types'], [AuthType.MATCH_VIDEO, AuthType.EVENT_TEAMS])

        # Ensure we show a success message on the page
        request = response.request
        self.assertEqual(request.GET.get('status'), 'success')

    def test_no_event(self):
        self.loginUser()
        form = self.getSuggestionForm()
        form['event_key'] = ''
        form['role'] = 'Test Code'
        response = form.submit().follow()
        self.assertEqual(response.status_int, 200)

        request = response.request
        self.assertEqual(request.GET.get('status'), 'bad_event')

    def test_non_existent_event(self):
        self.loginUser()
        form = self.getSuggestionForm()
        form['event_key'] = '2016foobar'
        form['role'] = 'Test Code'
        response = form.submit().follow()
        self.assertEqual(response.status_int, 200)

        request = response.request
        self.assertEqual(request.GET.get('status'), 'bad_event')
