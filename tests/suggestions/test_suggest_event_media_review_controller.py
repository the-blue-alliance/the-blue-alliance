import unittest2
import webapp2
import webtest
from google.appengine.datastore import datastore_stub_util
from google.appengine.ext import ndb
from google.appengine.ext import testbed
from webapp2_extras.routes import RedirectRoute

from consts.account_permissions import AccountPermissions
from consts.media_type import MediaType
from controllers.suggestions.suggest_event_media_review_controller import \
    SuggestEventMediaReviewController
from helpers.suggestions.suggestion_creator import SuggestionCreator
from models.account import Account
from models.event import Event
from models.media import Media
from models.suggestion import Suggestion


class TestSuggestEventWebcastController(unittest2.TestCase):

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
        self.account.permissions.append(AccountPermissions.REVIEW_EVENT_MEDIA)
        self.account.put()

    def createSuggestion(self):
        status = SuggestionCreator.createEventMediaSuggestion(self.account.key,
                                                             'https://www.youtube.com/watch?v=foobar',
                                                             '2016nyny')
        self.assertEqual(status[0], 'success')
        return Suggestion.query().fetch(keys_only=True)[0].id()

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
            RedirectRoute(r'/suggest/event/media/review', SuggestEventMediaReviewController, 'review-event-media', strict_slash=True),
        ], debug=True)
        self.testapp = webtest.TestApp(app)

    def tearDown(self):
        self.testbed.deactivate()

    def getSuggestionForm(self):
        response = self.testapp.get('/suggest/event/media/review')
        self.assertEqual(response.status_int, 200)

        form = response.forms.get('review_media', None)
        self.assertIsNotNone(form)
        return form

    def testLogInRedirect(self):
        response = self.testapp.get('/suggest/event/media/review', status='3*')
        response = response.follow(expect_errors=True)
        self.assertTrue(response.request.path.startswith("/account/login_required"))

    def testNoPermissions(self):
        self.loginUser()
        response = self.testapp.get('/suggest/event/media/review', status='3*')
        response = response.follow(expect_errors=True)
        self.assertEqual(response.request.path, '/')

    def testNothingToReview(self):
        self.loginUser()
        self.givePermission()
        response = self.testapp.get('/suggest/event/media/review')
        self.assertEqual(response.status_int, 200)

    def testAcceptSuggestion(self):
        self.loginUser()
        self.givePermission()
        suggestion_id = self.createSuggestion()
        form = self.getSuggestionForm()
        form['accept_reject-{}'.format(suggestion_id)] = 'accept::{}'.format(suggestion_id)
        response = form.submit().follow()
        self.assertEqual(response.status_int, 200)

        suggestion = Suggestion.get_by_id(suggestion_id)
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion.review_state, Suggestion.REVIEW_ACCEPTED)

        medias = Media.query().fetch()
        self.assertEqual(len(medias), 1)
        media = medias[0]
        self.assertIsNotNone(media)
        self.assertEqual(media.foreign_key, 'foobar')
        self.assertEqual(media.media_type_enum, MediaType.YOUTUBE_VIDEO)
        self.assertTrue(ndb.Key(Event, '2016nyny') in media.references)

    def testRejectSuggestion(self):
        self.loginUser()
        self.givePermission()
        suggestion_id = self.createSuggestion()
        form = self.getSuggestionForm()
        form['accept_reject-{}'.format(suggestion_id)] = 'reject::{}'.format(suggestion_id)
        response = form.submit().follow()
        self.assertEqual(response.status_int, 200)

        suggestion = Suggestion.get_by_id(suggestion_id)
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion.review_state, Suggestion.REVIEW_REJECTED)

        medias = Media.query().fetch()
        self.assertEqual(len(medias), 0)
