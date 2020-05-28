import unittest2
import webapp2
import webtest
from datetime import datetime

from google.appengine.datastore import datastore_stub_util
from google.appengine.ext import ndb
from google.appengine.ext import testbed
from webapp2_extras.routes import RedirectRoute

from consts.account_permissions import AccountPermissions
from consts.district_type import DistrictType
from consts.event_type import EventType
from controllers.suggestions.suggest_match_video_review_controller import \
    SuggestMatchVideoReviewController
from helpers.suggestions.suggestion_creator import SuggestionCreator
from models.account import Account
from models.event import Event
from models.match import Match
from models.suggestion import Suggestion


class TestSuggestMatchVideoReviewController(unittest2.TestCase):
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
            RedirectRoute(r'/suggest/match/video/review', SuggestMatchVideoReviewController, 'suggest-video', strict_slash=True),
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

        self.match = Match(
            id="2016necmp_f1m1",
            event=ndb.Key(Event, "2016necmp"),
            year=2016,
            comp_level="f",
            set_number=1,
            match_number=1,
            team_key_names=['frc846', 'frc2135', 'frc971', 'frc254', 'frc1678', 'frc973'],
            time=datetime.fromtimestamp(1409527874),
            time_string="4:31 PM",
            tba_videos=[],
            alliances_json='{\
                "blue": {\
                    "score": 270,\
                    "teams": [\
                    "frc846",\
                    "frc2135",\
                    "frc971"]},\
                "red": {\
                    "score": 310,\
                    "teams": [\
                    "frc254",\
                    "frc1678",\
                    "frc973"]}}',
            score_breakdown_json='{\
                "blue": {\
                    "auto": 70,\
                    "teleop_goal+foul": 40,\
                    "assist": 120,\
                    "truss+catch": 40\
                },"red": {\
                    "auto": 70,\
                    "teleop_goal+foul": 50,\
                    "assist": 150,\
                    "truss+catch": 40}}'
        )
        self.match.put()

        self.match2 = Match(
            id="2016necmp_f1m2",
            event=ndb.Key(Event, "2016necmp"),
            year=2016,
            comp_level="f",
            set_number=1,
            match_number=2,
            team_key_names=['frc846', 'frc2135', 'frc971', 'frc254', 'frc1678', 'frc973'],
            time=datetime.fromtimestamp(1409527874),
            time_string="4:31 PM",
            tba_videos=[],
            alliances_json='{\
                "blue": {\
                    "score": 270,\
                    "teams": [\
                    "frc846",\
                    "frc2135",\
                    "frc971"]},\
                "red": {\
                    "score": 310,\
                    "teams": [\
                    "frc254",\
                    "frc1678",\
                    "frc973"]}}',
            score_breakdown_json='{\
                "blue": {\
                    "auto": 70,\
                    "teleop_goal+foul": 40,\
                    "assist": 120,\
                    "truss+catch": 40\
                },"red": {\
                    "auto": 70,\
                    "teleop_goal+foul": 50,\
                    "assist": 150,\
                    "truss+catch": 40}}'
        )
        self.match2.put()

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
        self.account.permissions.append(AccountPermissions.REVIEW_MEDIA)
        self.account.put()

    def createSuggestion(self):
        status = SuggestionCreator.createMatchVideoYouTubeSuggestion(self.account.key,
                                                                     "H-54KMwMKY0",
                                                                     "2016necmp_f1m1")
        self.assertEqual(status, 'success')
        return Suggestion.render_media_key_name(2016, 'match', '2016necmp_f1m1', 'youtube', 'H-54KMwMKY0')

    def getSuggestionForm(self):
        response = self.testapp.get('/suggest/match/video/review')
        self.assertEqual(response.status_int, 200)

        form = response.forms.get('review_videos', None)
        self.assertIsNotNone(form)
        return form

    def test_login_redirect(self):
        response = self.testapp.get('/suggest/match/video/review', status='3*')
        response = response.follow(expect_errors=True)
        self.assertTrue(response.request.path.startswith("/account/login_required"))

    def test_no_permissions(self):
        self.loginUser()
        response = self.testapp.get('/suggest/match/video/review', status='3*')
        response = response.follow(expect_errors=True)
        self.assertEqual(response.request.path, '/')

    def test_nothing_to_review(self):
        self.loginUser()
        self.givePermission()
        response = self.testapp.get('/suggest/match/video/review')
        self.assertEqual(response.status_int, 200)

    def test_accept_suggestion(self):
        self.loginUser()
        self.givePermission()
        suggestion_id = self.createSuggestion()
        form = self.getSuggestionForm()
        form['accept_reject-{}'.format(suggestion_id)] = 'accept::{}'.format(suggestion_id)
        response = form.submit().follow()
        self.assertEqual(response.status_int, 200)

        # Make sure we mark the Suggestion as REVIEWED
        suggestion = Suggestion.get_by_id(suggestion_id)
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion.review_state, Suggestion.REVIEW_ACCEPTED)

        # Make sure the video gets associated
        match = Match.get_by_id(self.match.key_name)
        self.assertIsNotNone(match)
        self.assertIsNotNone(match.youtube_videos)
        self.assertTrue('H-54KMwMKY0' in match.youtube_videos)

    def test_accept_new_key(self):
        self.loginUser()
        self.givePermission()
        suggestion_id = self.createSuggestion()
        form = self.getSuggestionForm()
        form['accept_reject-{}'.format(suggestion_id)] = 'accept::{}'.format(suggestion_id)
        form['key-{}'.format(suggestion_id)] = '2016necmp_f1m2'
        response = form.submit().follow()
        self.assertEqual(response.status_int, 200)

        # Make sure we mark the Suggestion as REVIEWED
        suggestion = Suggestion.get_by_id(suggestion_id)
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion.review_state, Suggestion.REVIEW_ACCEPTED)

        # Make sure the video gets associated
        match = Match.get_by_id(self.match2.key_name)
        self.assertIsNotNone(match)
        self.assertIsNotNone(match.youtube_videos)
        self.assertTrue('H-54KMwMKY0' in match.youtube_videos)

        # Make sure we don't add it to the first match
        match = Match.get_by_id(self.match.key_name)
        self.assertIsNotNone(match)
        self.assertIsNotNone(match.youtube_videos)
        self.assertFalse('H-54KMwMKY0' in match.youtube_videos)

    def test_accept_bad_key(self):
        self.loginUser()
        self.givePermission()
        suggestion_id = self.createSuggestion()
        form = self.getSuggestionForm()
        form['accept_reject-{}'.format(suggestion_id)] = 'accept::{}'.format(suggestion_id)
        form['key-{}'.format(suggestion_id)] = '2016necmp_f1m3'  # This match doesn't exist
        response = form.submit().follow()
        self.assertEqual(response.status_int, 200)

        # Make sure we don't mark the Suggestion as REVIEWED
        suggestion = Suggestion.get_by_id(suggestion_id)
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion.review_state, Suggestion.REVIEW_PENDING)

        # Make sure the video doesn't get associated
        match = Match.get_by_id(self.match.key_name)
        self.assertIsNotNone(match)
        self.assertIsNotNone(match.youtube_videos)
        self.assertFalse('H-54KMwMKY0' in match.youtube_videos)

    def test_reject_suggestion(self):
        self.loginUser()
        self.givePermission()
        suggestion_id = self.createSuggestion()
        form = self.getSuggestionForm()
        form['accept_reject-{}'.format(suggestion_id)] = 'reject::{}'.format(suggestion_id)
        response = form.submit().follow()
        self.assertEqual(response.status_int, 200)

        # Make sure we mark the Suggestion as REVIEWED
        suggestion = Suggestion.get_by_id(suggestion_id)
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion.review_state, Suggestion.REVIEW_REJECTED)

        # Make sure the video gets associated
        match = Match.get_by_id(self.match.key_name)
        self.assertIsNotNone(match)
        self.assertFalse(match.youtube_videos)
