import unittest2
import webapp2
import webtest
from datetime import datetime

from google.appengine.datastore import datastore_stub_util
from google.appengine.ext import deferred
from google.appengine.ext import ndb
from google.appengine.ext import testbed
from webapp2_extras.routes import RedirectRoute

from consts.account_permissions import AccountPermissions
from consts.district_type import DistrictType
from consts.event_type import EventType
from controllers.suggestions.suggest_event_webcast_review_controller import \
    SuggestEventWebcastReviewController
from helpers.suggestions.suggestion_creator import SuggestionCreator
from models.account import Account
from models.event import Event
from models.suggestion import Suggestion


class TestSuggestEventWebcastReviewController(unittest2.TestCase):
    def setUp(self):
        self.policy = datastore_stub_util.PseudoRandomHRConsistencyPolicy(probability=1)
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub(consistency_policy=self.policy)
        self.testbed.init_memcache_stub()
        self.testbed.init_user_stub()
        self.testbed.init_urlfetch_stub()
        self.testbed.init_taskqueue_stub(_all_queues_valid=True)
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        app = webapp2.WSGIApplication([
            RedirectRoute(r'/suggest/event/webcast/review', SuggestEventWebcastReviewController, 'review-webcast', strict_slash=True),
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
            overwrite=True)

        self.account = Account.get_or_insert(
            "123",
            email="user@example.com",
            registered=True)

    def givePermission(self):
        self.account.permissions.append(AccountPermissions.REVIEW_MEDIA)
        self.account.put()

    def createSuggestion(self):
        status = SuggestionCreator.createEventWebcastSuggestion(self.account.key,
                                                                'https://twitch.tv/frcgamesense',
                                                                '',
                                                                '2016necmp')
        self.assertEqual(status, 'success')
        return 'webcast_2016necmp_twitch_frcgamesense_None'

    def getSuggestionForm(self, form_id):
        response = self.testapp.get('/suggest/event/webcast/review')
        self.assertEqual(response.status_int, 200)

        form = response.forms.get(form_id, None)
        self.assertIsNotNone(form)
        return form

    def test_login_redirect(self):
        response = self.testapp.get('/suggest/event/webcast/review', status='3*')
        response = response.follow(expect_errors=True)
        self.assertTrue(response.request.path.startswith("/account/login_required"))

    def test_no_permissions(self):
        self.loginUser()
        response = self.testapp.get('/suggest/event/webcast/review', status='3*')
        response = response.follow(expect_errors=True)
        self.assertEqual(response.request.path, '/')

    def test_nothing_to_review(self):
        self.loginUser()
        self.givePermission()
        response = self.testapp.get('/suggest/event/webcast/review')
        self.assertEqual(response.status_int, 200)

    def test_reject_all(self):
        self.loginUser()
        self.givePermission()
        suggestion_id = self.createSuggestion()
        form = self.getSuggestionForm('reject_all_2016necmp')
        response = form.submit('verdict', value='reject_all').follow()
        self.assertEqual(response.status_int, 200)

        request = response.request
        self.assertEqual(request.GET.get('success'), 'reject_all')

        # Make sure we mark the Suggestion as REVIEWED
        suggestion = Suggestion.get_by_id(suggestion_id)
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion.review_state, Suggestion.REVIEW_REJECTED)

        # Make sure the Event has no webcasts
        event = Event.get_by_id('2016necmp')
        self.assertIsNone(event.webcast)

    def test_accept_with_default_details(self):
        self.loginUser()
        self.givePermission()
        suggestion_id = self.createSuggestion()
        form = self.getSuggestionForm('review_{}'.format(suggestion_id))
        response = form.submit('verdict', value='accept').follow()
        self.assertEqual(response.status_int, 200)

        request = response.request
        self.assertEqual(request.GET.get('success'), 'accept')

        # Process task queue
        tasks = self.testbed.get_stub(testbed.TASKQUEUE_SERVICE_NAME).get_filtered_tasks()
        for task in tasks:
            deferred.run(task.payload)

        # Make sure we mark the Suggestion as REVIEWED
        suggestion = Suggestion.get_by_id(suggestion_id)
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion.review_state, Suggestion.REVIEW_ACCEPTED)

        # Make sure the Event has no webcasts
        event = Event.get_by_id('2016necmp')
        self.assertIsNotNone(event.webcast)
        self.assertEqual(len(event.webcast), 1)

        webcast = event.webcast[0]
        self.assertEqual(webcast['type'], 'twitch')
        self.assertEqual(webcast['channel'], 'frcgamesense')

    def test_accept_with_different_details(self):
        self.loginUser()
        self.givePermission()
        suggestion_id = self.createSuggestion()
        form = self.getSuggestionForm('review_{}'.format(suggestion_id))
        form['webcast_type'] = 'youtube'
        form['webcast_channel'] = 'foobar'
        form['webcast_file'] = 'meow'
        response = form.submit('verdict', value='accept').follow()
        self.assertEqual(response.status_int, 200)

        request = response.request
        self.assertEqual(request.GET.get('success'), 'accept')

        # Process task queue
        tasks = self.testbed.get_stub(testbed.TASKQUEUE_SERVICE_NAME).get_filtered_tasks()
        for task in tasks:
            deferred.run(task.payload)

        # Make sure we mark the Suggestion as REVIEWED
        suggestion = Suggestion.get_by_id(suggestion_id)
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion.review_state, Suggestion.REVIEW_ACCEPTED)

        # Make sure the Event has no webcasts
        event = Event.get_by_id('2016necmp')
        self.assertIsNotNone(event.webcast)
        self.assertEqual(len(event.webcast), 1)

        webcast = event.webcast[0]
        self.assertEqual(webcast['type'], 'youtube')
        self.assertEqual(webcast['channel'], 'foobar')
        self.assertEqual(webcast['file'], 'meow')

    def test_reject_single_webcast(self):
        self.loginUser()
        self.givePermission()
        suggestion_id = self.createSuggestion()
        form = self.getSuggestionForm('review_{}'.format(suggestion_id))
        response = form.submit('verdict', value='reject').follow()
        self.assertEqual(response.status_int, 200)

        request = response.request
        self.assertEqual(request.GET.get('success'), 'reject')

        # Make sure we mark the Suggestion as REVIEWED
        suggestion = Suggestion.get_by_id(suggestion_id)
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion.review_state, Suggestion.REVIEW_REJECTED)

        # Make sure the Event has no webcasts
        event = Event.get_by_id('2016necmp')
        self.assertIsNone(event.webcast)
