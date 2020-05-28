import datetime
import unittest2
import webapp2
import webtest

from google.appengine.datastore import datastore_stub_util
from google.appengine.ext import ndb
from google.appengine.ext import testbed
from webapp2_extras.routes import RedirectRoute

from consts.account_permissions import AccountPermissions
from consts.media_type import MediaType
from controllers.team_admin_controller import TeamAdminDashboard, TeamAdminRedeem
from controllers.suggestions.suggest_designs_review_controller import SuggestDesignsReviewController
from controllers.suggestions.suggest_team_media_review_controller import \
    SuggestTeamMediaReviewController
from controllers.suggestions.suggest_social_media_review_controller import \
    SuggestSocialMediaReviewController
from helpers.suggestions.media_creator import MediaCreator
from helpers.suggestions.suggestion_creator import SuggestionCreator
from models.account import Account
from models.media import Media
from models.robot import Robot
from models.suggestion import Suggestion
from models.team import Team
from models.team_admin_access import TeamAdminAccess


class TestSuggestTeamAdminSuggestionReview(unittest2.TestCase):
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

        app = webapp2.WSGIApplication(
            [
                RedirectRoute(
                    r'/mod',
                    TeamAdminDashboard,
                    'team-admin',
                    strict_slash=True),
                RedirectRoute(
                    r'/mod/redeem',
                    TeamAdminRedeem,
                    'team-admin',
                    strict_slash=True),
                RedirectRoute(
                    r'/suggest/cad/review',
                    SuggestDesignsReviewController,
                    'review-designs',
                    strict_slash=True),
                RedirectRoute(
                    r'/suggest/team/media/review',
                    SuggestTeamMediaReviewController,
                    'review-media',
                    strict_slash=True),
                RedirectRoute(
                    r'/suggest/team/social/review',
                    SuggestSocialMediaReviewController,
                    'review-social',
                    strict_slash=True),
            ],
            debug=True)
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

    def giveTeamAdminAccess(self, expiration_days=1):
        access = TeamAdminAccess(
            id="test_access",
            team_number=1124,
            year=self.now.year,
            expiration=self.now + datetime.timedelta(days=expiration_days),
            account=self.account.key,
        )
        return access.put()

    def createMediaSuggestion(self):
        status = SuggestionCreator.createTeamMediaSuggestion(
            self.account.key, 'http://imgur.com/foobar', 'frc1124',
            self.now.year)
        self.assertEqual(status[0], 'success')
        return Suggestion.query().fetch(keys_only=True)[0].id()

    def createSocialMediaSuggestion(self):
        status = SuggestionCreator.createTeamMediaSuggestion(
            self.account.key, 'http://twitter.com/frc1124', 'frc1124', None,
            None, True)
        self.assertEqual(status[0], 'success')
        return Suggestion.query().fetch(keys_only=True)[0].id()

    def createDesignSuggestion(self):
        status = SuggestionCreator.createTeamMediaSuggestion(
            self.account.key,
            'https://grabcad.com/library/2016-148-robowranglers-1', 'frc1124',
            '2016')
        self.assertEqual(status[0], 'success')
        return Suggestion.render_media_key_name(
            '2016', 'team', 'frc1124', 'grabcad', '2016-148-robowranglers-1')

    def getSuggestionForm(self, suggestion_type):
        response = self.testapp.get('/mod')
        self.assertEqual(response.status_int, 200)

        form = response.forms.get('review_{}'.format(suggestion_type), None)
        self.assertIsNotNone(form)
        return form

    def getMediaAdminForm(self, action, media_key_name):
        response = self.testapp.get('/mod')
        self.assertEqual(response.status_int, 200)

        form = response.forms.get('{}_{}'.format(action, media_key_name), None)
        self.assertIsNotNone(form)
        return form

    def getTeamInfoForm(self, team_number):
        response = self.testapp.get('/mod')
        self.assertEqual(response.status_int, 200)

        form = response.forms.get('team-info-frc{}'.format(team_number), None)
        self.assertIsNotNone(form)
        return form

    def test_login_redirect(self):
        response = self.testapp.get('/mod', status='3*')
        response = response.follow(expect_errors=True)
        self.assertTrue(
            response.request.path.startswith("/account/login_required"))

    def test_no_access(self):
        self.loginUser()
        response = self.testapp.get('/mod', status='3*').follow()
        self.assertEqual(response.status_int, 200)
        self.assertEqual(response.request.path, "/mod/redeem")

    def test_expired_access(self):
        self.loginUser()
        self.giveTeamAdminAccess(expiration_days=-1)
        response = self.testapp.get('/mod', status='3*').follow()
        self.assertEqual(response.status_int, 200)
        self.assertEqual(response.request.path, "/mod/redeem")

    def test_nothing_to_review(self):
        self.loginUser()
        self.giveTeamAdminAccess()
        response = self.testapp.get('/mod')
        self.assertEqual(response.status_int, 200)

    """
    Test moderating existing media items (remove reference, manage preferred)
    """

    def test_manage_media_expired_auth(self):
        self.loginUser()
        access_key = self.giveTeamAdminAccess()

        team_reference = Media.create_reference('team', 'frc1124')
        suggestion_id = self.createSocialMediaSuggestion()
        suggestion = Suggestion.get_by_id(suggestion_id)
        media = MediaCreator.create_media_model(suggestion, team_reference)
        media_id = media.put()
        self.assertTrue(ndb.Key(Team, 'frc1124') in media.references)

        form = self.getMediaAdminForm('remove_media', media_id.id())
        access = access_key.get()
        access.expiration += datetime.timedelta(days=-7)
        access.put()

        response = form.submit(status='403', expect_errors=True)
        self.assertEqual(response.status_int, 403)

    def test_remove_social_media_reference(self):
        self.loginUser()
        self.giveTeamAdminAccess()

        team_reference = Media.create_reference('team', 'frc1124')
        suggestion_id = self.createSocialMediaSuggestion()
        suggestion = Suggestion.get_by_id(suggestion_id)
        media = MediaCreator.create_media_model(suggestion, team_reference)
        media_id = media.put()
        self.assertTrue(ndb.Key(Team, 'frc1124') in media.references)

        form = self.getMediaAdminForm('remove_media', media_id.id())
        response = form.submit().follow()
        self.assertEqual(response.status_int, 301)

        media = media_id.get()
        self.assertFalse(team_reference in media.references)

    def test_remove_media_reference(self):
        self.loginUser()
        self.giveTeamAdminAccess()

        team_reference = Media.create_reference('team', 'frc1124')
        suggestion_id = self.createMediaSuggestion()
        suggestion = Suggestion.get_by_id(suggestion_id)
        media = MediaCreator.create_media_model(suggestion, team_reference)
        media_id = media.put()
        self.assertTrue(ndb.Key(Team, 'frc1124') in media.references)

        form = self.getMediaAdminForm('remove_media', media_id.id())
        response = form.submit().follow()
        self.assertEqual(response.status_int, 301)

        media = media_id.get()
        self.assertFalse(team_reference in media.references)

    def test_make_media_preferred(self):
        self.loginUser()
        self.giveTeamAdminAccess()

        team_reference = Media.create_reference('team', 'frc1124')
        suggestion_id = self.createMediaSuggestion()
        suggestion = Suggestion.get_by_id(suggestion_id)
        media = MediaCreator.create_media_model(suggestion, team_reference)
        media_id = media.put()
        self.assertTrue(ndb.Key(Team, 'frc1124') in media.references)

        form = self.getMediaAdminForm('add_preferred', media_id.id())
        response = form.submit().follow()
        self.assertEqual(response.status_int, 301)

        media = media_id.get()
        self.assertTrue(team_reference in media.references)
        self.assertTrue(team_reference in media.preferred_references)

    def test_remove_media_preferred(self):
        self.loginUser()
        self.giveTeamAdminAccess()

        team_reference = Media.create_reference('team', 'frc1124')
        suggestion_id = self.createMediaSuggestion()
        suggestion = Suggestion.get_by_id(suggestion_id)
        media = MediaCreator.create_media_model(suggestion, team_reference)
        media.preferred_references.append(team_reference)
        media_id = media.put()
        self.assertTrue(ndb.Key(Team, 'frc1124') in media.references)

        form = self.getMediaAdminForm('remove_preferred', media_id.id())
        response = form.submit().follow()
        self.assertEqual(response.status_int, 301)

        media = media_id.get()
        self.assertTrue(team_reference in media.references)
        self.assertFalse(team_reference in media.preferred_references)

    """
    Test modifying team properties
    """

    def test_set_robot_name(self):
        self.loginUser()
        self.giveTeamAdminAccess()

        # There is no Robot models that exists yet for this team
        form = self.getTeamInfoForm(1124)
        form['robot_name'] = 'Test Robot Name'
        response = form.submit().follow()
        self.assertEqual(response.status_int, 301)

        robot = Robot.get_by_id(Robot.renderKeyName('frc1124', self.now.year))
        self.assertIsNotNone(robot)
        self.assertEqual(robot.robot_name, 'Test Robot Name')

    def test_update_robot_name(self):
        self.loginUser()
        self.giveTeamAdminAccess()

        Robot(
            id=Robot.renderKeyName(self.team.key_name, self.now.year),
            team=self.team.key,
            year=self.now.year,
            robot_name='First Robot Name',
        ).put()

        form = self.getTeamInfoForm(1124)
        self.assertEqual(form['robot_name'].value, 'First Robot Name')
        form['robot_name'] = 'Second Robot Name'
        response = form.submit().follow()
        self.assertEqual(response.status_int, 301)

        robot = Robot.get_by_id(Robot.renderKeyName('frc1124', self.now.year))
        self.assertIsNotNone(robot)
        self.assertEqual(robot.robot_name, 'Second Robot Name')

    def test_delete_robot_name(self):
        self.loginUser()
        self.giveTeamAdminAccess()

        Robot(
            id=Robot.renderKeyName(self.team.key_name, self.now.year),
            team=self.team.key,
            year=self.now.year,
            robot_name='First Robot Name',
        ).put()

        form = self.getTeamInfoForm(1124)
        self.assertEqual(form['robot_name'].value, 'First Robot Name')
        form['robot_name'] = ''
        response = form.submit().follow()
        self.assertEqual(response.status_int, 301)

        robot = Robot.get_by_id(Robot.renderKeyName('frc1124', self.now.year))
        self.assertIsNone(robot)

    """
    Test accepting/rejecting suggestions for the given team
    These are basically the same tests as the individual suggestion review
    controller tests, but since we post to that same URL, we'll want to make
    sure everything works from both paths
    """

    def test_accept_team_media_expired_auth(self):
        self.loginUser()
        access_key = self.giveTeamAdminAccess()

        suggestion_id = self.createMediaSuggestion()
        form = self.getSuggestionForm('media')
        form['accept_reject-{}'.format(suggestion_id)] = 'accept::{}'.format(
            suggestion_id)
        access = access_key.get()
        access.expiration += datetime.timedelta(days=-7)
        access.put()
        response = form.submit().follow(expect_errors=True)
        self.assertEqual(response.request.path, "/")

        suggestion = Suggestion.get_by_id(suggestion_id)
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion.review_state, Suggestion.REVIEW_PENDING)

    def test_reject_team_media_expired_auth(self):
        self.loginUser()
        access_key = self.giveTeamAdminAccess()

        suggestion_id = self.createMediaSuggestion()
        form = self.getSuggestionForm('media')
        form['accept_reject-{}'.format(suggestion_id)] = 'reject::{}'.format(
            suggestion_id)
        access = access_key.get()
        access.expiration += datetime.timedelta(days=-7)
        access.put()
        response = form.submit().follow(expect_errors=True)
        self.assertEqual(response.request.path, "/")

        suggestion = Suggestion.get_by_id(suggestion_id)
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion.review_state, Suggestion.REVIEW_PENDING)

    def test_accept_team_media(self):
        self.loginUser()
        self.giveTeamAdminAccess()

        suggestion_id = self.createMediaSuggestion()
        form = self.getSuggestionForm('media')
        form['accept_reject-{}'.format(suggestion_id)] = 'accept::{}'.format(
            suggestion_id)
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
        self.assertEqual(media.media_type_enum, MediaType.IMGUR)
        self.assertTrue(ndb.Key(Team, 'frc1124') in media.references)

    def test_accept_team_media_as_preferred(self):
        self.loginUser()
        self.giveTeamAdminAccess()

        suggestion_id = self.createMediaSuggestion()
        form = self.getSuggestionForm('media')
        form['accept_reject-{}'.format(suggestion_id)] = 'accept::{}'.format(
            suggestion_id)
        form['preferred_keys[]'] = ['preferred::{}'.format(suggestion_id)]
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
        self.assertEqual(media.media_type_enum, MediaType.IMGUR)
        self.assertTrue(ndb.Key(Team, 'frc1124') in media.preferred_references)

    def test_reject_team_media(self):
        self.loginUser()
        self.giveTeamAdminAccess()

        suggestion_id = self.createMediaSuggestion()
        form = self.getSuggestionForm('media')
        form['accept_reject-{}'.format(suggestion_id)] = 'reject::{}'.format(
            suggestion_id)
        response = form.submit().follow()
        self.assertEqual(response.status_int, 200)

        suggestion = Suggestion.get_by_id(suggestion_id)
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion.review_state, Suggestion.REVIEW_REJECTED)

        medias = Media.query().fetch()
        self.assertEqual(len(medias), 0)

    def test_accept_social_media_expired_auth(self):
        self.loginUser()
        access_key = self.giveTeamAdminAccess()

        suggestion_id = self.createSocialMediaSuggestion()
        form = self.getSuggestionForm('social-media')
        form['accept_reject-{}'.format(suggestion_id)] = 'accept::{}'.format(
            suggestion_id)
        access = access_key.get()
        access.expiration += datetime.timedelta(days=-7)
        access.put()
        response = form.submit().follow(expect_errors=True)
        self.assertEqual(response.request.path, "/")

        suggestion = Suggestion.get_by_id(suggestion_id)
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion.review_state, Suggestion.REVIEW_PENDING)

    def test_reject_social_media_expired_auth(self):
        self.loginUser()
        access_key = self.giveTeamAdminAccess()

        suggestion_id = self.createSocialMediaSuggestion()
        form = self.getSuggestionForm('social-media')
        form['accept_reject-{}'.format(suggestion_id)] = 'reject::{}'.format(
            suggestion_id)
        access = access_key.get()
        access.expiration += datetime.timedelta(days=-7)
        access.put()
        response = form.submit().follow(expect_errors=True)
        self.assertEqual(response.request.path, "/")

        suggestion = Suggestion.get_by_id(suggestion_id)
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion.review_state, Suggestion.REVIEW_PENDING)

    def test_accept_social_media(self):
        self.loginUser()
        self.giveTeamAdminAccess()

        suggestion_id = self.createSocialMediaSuggestion()
        form = self.getSuggestionForm('social-media')
        form['accept_reject-{}'.format(suggestion_id)] = 'accept::{}'.format(
            suggestion_id)
        response = form.submit().follow()
        self.assertEqual(response.status_int, 200)

        suggestion = Suggestion.get_by_id(suggestion_id)
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion.review_state, Suggestion.REVIEW_ACCEPTED)

        medias = Media.query().fetch()
        self.assertEqual(len(medias), 1)
        media = medias[0]
        self.assertIsNotNone(media)
        self.assertEqual(media.foreign_key, 'frc1124')
        self.assertEqual(media.media_type_enum, MediaType.TWITTER_PROFILE)
        self.assertTrue(ndb.Key(Team, 'frc1124') in media.references)

    def test_reject_social_media(self):
        self.loginUser()
        self.giveTeamAdminAccess()

        suggestion_id = self.createSocialMediaSuggestion()
        form = self.getSuggestionForm('social-media')
        form['accept_reject-{}'.format(suggestion_id)] = 'reject::{}'.format(
            suggestion_id)
        response = form.submit().follow()
        self.assertEqual(response.status_int, 200)

        suggestion = Suggestion.get_by_id(suggestion_id)
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion.review_state, Suggestion.REVIEW_REJECTED)

        medias = Media.query().fetch()
        self.assertEqual(len(medias), 0)

    def test_accept_robot_design_expired_auth(self):
        self.loginUser()
        access_key = self.giveTeamAdminAccess()

        suggestion_id = self.createDesignSuggestion()
        form = self.getSuggestionForm('robot')
        form['accept_reject-{}'.format(suggestion_id)] = 'accept::{}'.format(
            suggestion_id)
        access = access_key.get()
        access.expiration += datetime.timedelta(days=-7)
        access.put()
        response = form.submit().follow(expect_errors=True)
        self.assertEqual(response.request.path, "/")

        suggestion = Suggestion.get_by_id(suggestion_id)
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion.review_state, Suggestion.REVIEW_PENDING)

    def test_reject_robot_design_expired_auth(self):
        self.loginUser()
        access_key = self.giveTeamAdminAccess()

        suggestion_id = self.createDesignSuggestion()
        form = self.getSuggestionForm('robot')
        form['accept_reject-{}'.format(suggestion_id)] = 'reject::{}'.format(
            suggestion_id)
        access = access_key.get()
        access.expiration += datetime.timedelta(days=-7)
        access.put()
        response = form.submit().follow(expect_errors=True)
        self.assertEqual(response.request.path, "/")

        suggestion = Suggestion.get_by_id(suggestion_id)
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion.review_state, Suggestion.REVIEW_PENDING)

    def test_accept_robot_design(self):
        self.loginUser()
        self.giveTeamAdminAccess()

        suggestion_id = self.createDesignSuggestion()
        form = self.getSuggestionForm('robot')
        form['accept_reject-{}'.format(suggestion_id)] = 'accept::{}'.format(
            suggestion_id)
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

    def test_reject_robot_design(self):
        self.loginUser()
        self.giveTeamAdminAccess()

        suggestion_id = self.createDesignSuggestion()
        form = self.getSuggestionForm('robot')
        form['accept_reject-{}'.format(suggestion_id)] = 'reject::{}'.format(
            suggestion_id)
        response = form.submit().follow()
        self.assertEqual(response.status_int, 200)

        # Make sure the Media object doesn't get created
        medias = Media.query().fetch(keys_only=True)
        self.assertEqual(len(medias), 0)

        # Make sure we mark the Suggestion as REVIEWED
        suggestion = Suggestion.get_by_id(suggestion_id)
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion.review_state, Suggestion.REVIEW_REJECTED)
