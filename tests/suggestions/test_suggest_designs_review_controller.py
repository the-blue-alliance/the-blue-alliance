import unittest2
import webapp2
import webtest

from google.appengine.datastore import datastore_stub_util
from google.appengine.ext import ndb
from google.appengine.ext import testbed
from webapp2_extras.routes import RedirectRoute

from consts.account_permissions import AccountPermissions
from consts.media_type import MediaType
from controllers.suggestions.suggest_designs_review_controller import SuggestDesignsReviewController
from controllers.suggestions.suggest_review_home_controller import SuggestReviewHomeController
from helpers.suggestions.suggestion_creator import SuggestionCreator
from models.account import Account
from models.media import Media
from models.suggestion import Suggestion
from models.team import Team


class TestSuggestDesignsReviewController(unittest2.TestCase):
    def setUp(self):
        self.policy = datastore_stub_util.PseudoRandomHRConsistencyPolicy(probability=1)
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub(consistency_policy=self.policy)
        self.testbed.init_memcache_stub()
        self.testbed.init_user_stub()
        self.testbed.init_urlfetch_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        self.testbed.init_taskqueue_stub(root_path='.')
        self.taskqueue_stub = self.testbed.get_stub(testbed.TASKQUEUE_SERVICE_NAME)

        app = webapp2.WSGIApplication([
            RedirectRoute(r'/suggest/cad/review', SuggestDesignsReviewController, 'review-designs', strict_slash=True),
            RedirectRoute(r'/suggest/review', SuggestReviewHomeController, 'review-home', strict_slash=True),
        ], debug=True)
        self.testapp = webtest.TestApp(app)

        self.team = Team(
            id="frc1124",
            team_number=1124,
        )
        self.team.put()

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
        self.account.permissions.append(AccountPermissions.REVIEW_DESIGNS)
        self.account.put()

    def createSuggestion(self):
        status = SuggestionCreator.createTeamMediaSuggestion(self.account.key,
                                                             'https://grabcad.com/library/2016-148-robowranglers-1',
                                                             'frc1124',
                                                             '2016')
        self.assertEqual(status[0], 'success')
        return Suggestion.render_media_key_name('2016', 'team', 'frc1124', 'grabcad', '2016-148-robowranglers-1')

    def getSuggestionForm(self):
        response = self.testapp.get('/suggest/cad/review')
        self.assertEqual(response.status_int, 200)

        form = response.forms.get('review_designs', None)
        self.assertIsNotNone(form)
        return form

    def test_login_redirect(self):
        response = self.testapp.get('/suggest/cad/review', status='3*')
        response = response.follow(expect_errors=True)
        self.assertTrue(response.request.path.startswith("/account/login_required"))

    def test_no_permissions(self):
        self.loginUser()
        response = self.testapp.get('/suggest/cad/review', status='3*')
        response = response.follow(expect_errors=True)
        self.assertEqual(response.request.path, '/')

    def test_nothing_to_review(self):
        self.loginUser()
        self.givePermission()
        form = self.getSuggestionForm()
        response = form.submit().follow()
        self.assertEqual(response.status_int, 200)

    def test_accept_suggestion(self):
        self.loginUser()
        self.givePermission()
        suggestion_id = self.createSuggestion()
        form = self.getSuggestionForm()
        form['accept_reject-{}'.format(suggestion_id)] = 'accept::{}'.format(suggestion_id)
        response = form.submit().follow()
        self.assertEqual(response.status_int, 200)

        # Make sure the Media object gets created
        media = Media.query().fetch()[0]
        self.assertIsNotNone(media)
        self.assertEqual(media.media_type_enum, MediaType.GRABCAD)
        self.assertEqual(media.year, 2016)
        self.assertListEqual(media.references, [self.team.key])

        # Make sure we mark the Suggestion as REVIEWED
        suggestion = Suggestion.get_by_id(suggestion_id)
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion.review_state, Suggestion.REVIEW_ACCEPTED)

    def test_reject_suggestion(self):
        self.loginUser()
        self.givePermission()
        suggestion_id = self.createSuggestion()
        form = self.getSuggestionForm()
        form['accept_reject-{}'.format(suggestion_id)] = 'reject::{}'.format(suggestion_id)
        response = form.submit().follow()
        self.assertEqual(response.status_int, 200)

        # Make sure the Media object doesn't get created
        medias = Media.query().fetch(keys_only=True)
        self.assertEqual(len(medias), 0)

        # Make sure we mark the Suggestion as REVIEWED
        suggestion = Suggestion.get_by_id(suggestion_id)
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion.review_state, Suggestion.REVIEW_REJECTED)

    def test_fast_path_accept(self):
        self.loginUser()
        self.givePermission()
        suggestion_id = self.createSuggestion()

        response = self.testapp.get('/suggest/cad/review?action=accept&id={}'.format(suggestion_id))
        response = response.follow()
        self.assertEqual(response.status_int, 200)
        self.assertEqual(response.request.GET.get('status'), 'accepted')

        # Make sure the Media object gets created
        media = Media.query().fetch()[0]
        self.assertIsNotNone(media)
        self.assertEqual(media.media_type_enum, MediaType.GRABCAD)
        self.assertEqual(media.year, 2016)
        self.assertListEqual(media.references, [self.team.key])

        suggestion = Suggestion.get_by_id(suggestion_id)
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion.review_state, Suggestion.REVIEW_ACCEPTED)

    def test_fast_path_reject(self):
        self.loginUser()
        self.givePermission()
        suggestion_id = self.createSuggestion()

        response = self.testapp.get('/suggest/cad/review?action=reject&id={}'.format(suggestion_id))
        response = response.follow()
        self.assertEqual(response.status_int, 200)
        self.assertEqual(response.request.GET.get('status'), 'rejected')

        medias = Media.query().fetch(keys_only=True)
        self.assertEqual(len(medias), 0)

        suggestion = Suggestion.get_by_id(suggestion_id)
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion.review_state, Suggestion.REVIEW_REJECTED)

    def test_fast_path_already_reviewed(self):
        self.loginUser()
        self.givePermission()
        suggestion_id = self.createSuggestion()

        suggestion = Suggestion.get_by_id(suggestion_id)
        suggestion.review_state = Suggestion.REVIEW_ACCEPTED
        suggestion.put()

        response = self.testapp.get('/suggest/cad/review?action=accept&id={}'.format(suggestion_id))
        response = response.follow()
        self.assertEqual(response.status_int, 200)
        self.assertEqual(response.request.GET.get('status'), 'already_reviewed')

    def test_fast_path_bad_id(self):
        self.loginUser()
        self.givePermission()
        response = self.testapp.get('/suggest/cad/review?action=accept&id=abc123')
        response = response.follow()
        self.assertEqual(response.status_int, 200)
        self.assertEqual(response.request.GET.get('status'), 'bad_suggestion')
