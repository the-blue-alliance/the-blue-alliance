import unittest2
import webapp2
import webtest
from datetime import datetime

from google.appengine.datastore import datastore_stub_util
from google.appengine.ext import ndb
from google.appengine.ext import testbed
from webapp2_extras.routes import RedirectRoute

from consts.account_permissions import AccountPermissions
from consts.auth_type import AuthType
from consts.district_type import DistrictType
from consts.event_type import EventType
from controllers.suggestions.suggest_apiwrite_review_controller import \
    SuggestApiWriteReviewController
from helpers.suggestions.suggestion_creator import SuggestionCreator
from models.account import Account
from models.api_auth_access import ApiAuthAccess
from models.event import Event
from models.suggestion import Suggestion


class TestSuggestApiWriteReviewController(unittest2.TestCase):
    def setUp(self):
        self.policy = datastore_stub_util.PseudoRandomHRConsistencyPolicy(probability=1)
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub(consistency_policy=self.policy)
        self.testbed.init_memcache_stub()
        self.testbed.init_user_stub()
        self.testbed.init_mail_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        app = webapp2.WSGIApplication([
            RedirectRoute(r'/suggest/apiwrite/review', SuggestApiWriteReviewController, 'review-apiwrite', strict_slash=True),
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

        self.account = Account.get_or_insert(
            "123",
            email="user@example.com",
            registered=True
        )

    def givePermission(self):
        self.account.permissions.append(AccountPermissions.REVIEW_APIWRITE)
        self.account.put()

    def createSuggestion(self):
        status = SuggestionCreator.createApiWriteSuggestion(self.account.key, '2016necmp', 'Test',
                                                            [AuthType.EVENT_MATCHES])
        self.assertEqual(status, 'success')
        return Suggestion.query(Suggestion.target_key == '2016necmp').fetch(keys_only=True)[0].id()

    def getSuggestionForm(self, suggestion_id):
        response = self.testapp.get('/suggest/apiwrite/review')
        self.assertEqual(response.status_int, 200)

        form = response.forms.get('apiwrite_review_{}'.format(suggestion_id), None)
        self.assertIsNotNone(form)
        return form

    def test_login_redirect(self):
        response = self.testapp.get('/suggest/apiwrite/review', status='3*')
        response = response.follow(expect_errors=True)
        self.assertTrue(response.request.path.startswith("/account/login_required"))

    def test_no_permissions(self):
        self.loginUser()
        response = self.testapp.get('/suggest/apiwrite/review', status='3*')
        response = response.follow(expect_errors=True)
        self.assertEqual(response.request.path, '/')

    def test_nothing_to_review(self):
        self.loginUser()
        self.givePermission()
        response = self.testapp.get('/suggest/apiwrite/review')
        self.assertEqual(response.status_int, 200)

        # Make sure none of the forms on the page are for suggestions
        for form_id in response.forms.keys():
            self.assertFalse("{}".format(form_id).startswith('apiwrite_review_'))

    def test_accespt_suggestion(self):
        self.loginUser()
        self.givePermission()
        suggestion_id = self.createSuggestion()
        form = self.getSuggestionForm(suggestion_id)
        response = form.submit('verdict', value='accept').follow()
        self.assertEqual(response.status_int, 200)

        # Make sure the ApiWrite object gets created
        auth = ApiAuthAccess.query().fetch()[0]
        self.assertIsNotNone(auth)
        self.assertEqual(auth.owner, self.account.key)
        self.assertListEqual(auth.event_list, [self.event.key])
        self.assertListEqual(auth.auth_types_enum, [AuthType.EVENT_MATCHES])
        self.assertIsNotNone(auth.secret)
        self.assertIsNotNone(auth.expiration)

        # Make sure we mark the Suggestion as REVIEWED
        suggestion = Suggestion.get_by_id(suggestion_id)
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion.review_state, Suggestion.REVIEW_ACCEPTED)

    def test_reject_suggestion(self):
        self.loginUser()
        self.givePermission()
        suggestion_id = self.createSuggestion()
        form = self.getSuggestionForm(suggestion_id)
        response = form.submit('verdict', value='reject').follow()
        self.assertEqual(response.status_int, 200)

        auths = ApiAuthAccess.query().fetch()
        self.assertEqual(len(auths), 0)

        # Make sure we mark the Suggestion as REJECTED
        suggestion = Suggestion.get_by_id(suggestion_id)
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion.review_state, Suggestion.REVIEW_REJECTED)

    def test_existing_auth_keys(self):
        self.loginUser()
        self.givePermission()

        existing_auth = ApiAuthAccess(id='tEsT_id_0',
                                      secret='321tEsTsEcReT',
                                      description='test',
                                      event_list=[ndb.Key(Event, '2016necmp')],
                                      auth_types_enum=[AuthType.EVENT_TEAMS])
        existing_auth.put()

        suggestion_id = self.createSuggestion()
        form = self.getSuggestionForm(suggestion_id)
        response = form.submit('verdict', value='accept').follow()
        self.assertEqual(response.status_int, 200)

        auths = ApiAuthAccess.query().fetch()
        self.assertTrue(len(auths), 2)

    def test_accept_suggestion_with_different_auth_types(self):
        self.loginUser()
        self.givePermission()
        suggestion_id = self.createSuggestion()
        form = self.getSuggestionForm(suggestion_id)
        form.get('auth_types', index=0).checked = True  # MATCH_VIDEO
        form.get('auth_types', index=1).checked = True  # EVENT_TEAMS
        form.get('auth_types', index=2).checked = False  # EVENT_MATCHES
        response = form.submit('verdict', value='accept').follow()
        self.assertEqual(response.status_int, 200)

        # Make sure the ApiWrite object gets created
        auth = ApiAuthAccess.query().fetch()[0]
        self.assertIsNotNone(auth)
        self.assertEqual(auth.owner, self.account.key)
        self.assertListEqual(auth.event_list, [self.event.key])
        self.assertSetEqual(set(auth.auth_types_enum), {AuthType.EVENT_TEAMS, AuthType.MATCH_VIDEO})
        self.assertIsNotNone(auth.secret)
        self.assertIsNotNone(auth.expiration)
