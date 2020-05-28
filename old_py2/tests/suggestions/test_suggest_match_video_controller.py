import unittest2
import webapp2
import webtest
from datetime import datetime

from google.appengine.ext import ndb
from google.appengine.ext import testbed
from webapp2_extras.routes import RedirectRoute

from consts.district_type import DistrictType
from consts.event_type import EventType
from controllers.suggestions.suggest_match_video_controller import SuggestMatchVideoController, \
    SuggestMatchVideoPlaylistController
from models.account import Account
from models.event import Event
from models.match import Match
from models.suggestion import Suggestion


class TestSuggestMatchVideoController(unittest2.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_user_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        app = webapp2.WSGIApplication([
            RedirectRoute(r'/suggest/match/video', SuggestMatchVideoController, 'suggest-match-video', strict_slash=True),
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
            youtube_videos=["JbwUzl3W9ug"],
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

    def getSuggestionForm(self, match_key):
        response = self.testapp.get('/suggest/match/video?match_key={}'.format(match_key))
        self.assertEqual(response.status_int, 200)

        form = response.forms.get('suggest_match_video', None)
        self.assertIsNotNone(form)
        return form

    def test_login_redirect(self):
        response = self.testapp.get('/suggest/match/video?match_key=2016necmp_f1m1', status='3*')
        response = response.follow(expect_errors=True)
        self.assertTrue(response.request.path.startswith("/account/login_required"))

    def test_no_params(self):
        self.loginUser()
        response = self.testapp.get('/suggest/match/video', status='3*')
        response = response.follow(expect_errors=True)
        self.assertEqual(response.request.path, '/')

    def test_submit_empty_form(self):
        self.loginUser()
        form = self.getSuggestionForm('2016necmp_f1m1')
        response = form.submit().follow()
        self.assertEqual(response.status_int, 200)

        request = response.request
        self.assertEqual(request.GET.get('status'), 'bad_url')

    def test_submit_match_video(self):
        self.loginUser()
        form = self.getSuggestionForm('2016necmp_f1m1')
        form['youtube_url'] = "http://youtu.be/bHGyTjxbLz8"
        response = form.submit().follow()
        self.assertEqual(response.status_int, 200)

        # Make sure the Suggestion gets created
        suggestion_id = "media_2016_match_2016necmp_f1m1_youtube_bHGyTjxbLz8"
        suggestion = Suggestion.get_by_id(suggestion_id)
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion.review_state, Suggestion.REVIEW_PENDING)

        # Ensure we show a success message on the page
        request = response.request
        self.assertEqual(request.GET.get('status'), 'success')


class TestSuggestMatchVideoPlaylistController(unittest2.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_user_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        app = webapp2.WSGIApplication([
            RedirectRoute(r'/suggest/event/video', SuggestMatchVideoPlaylistController, 'suggest-event-video', strict_slash=True),
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
            youtube_videos=["JbwUzl3W9ug"],
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
        response = self.testapp.get('/suggest/event/video?event_key={}'.format(event_key))
        self.assertEqual(response.status_int, 200)

        form = response.forms.get('event_videos', None)
        self.assertIsNotNone(form)
        return form

    def test_login_redirect(self):
        response = self.testapp.get('/suggest/event/video?event_key=2016necmp', status='3*')
        response = response.follow(expect_errors=True)
        self.assertTrue(response.request.path.startswith("/account/login_required"))

    def test_no_params(self):
        self.loginUser()
        response = self.testapp.get('/suggest/event/video', status='3*')
        response = response.follow(expect_errors=True)
        self.assertEqual(response.request.path, '/')

    def test_bad_event(self):
        self.loginUser()
        response = self.testapp.get('/suggest/event/video?event_key=2016foo', expect_errors=True)
        self.assertEqual(response.status_int, 404)

    def test_submit_empty_form(self):
        self.loginUser()
        form = self.getSuggestionForm('2016necmp')
        response = form.submit().follow()
        self.assertEqual(response.status_int, 200)

        request = response.request
        self.assertEqual(request.GET.get('num_added'), '0')

    def test_submit_one_video(self):
        self.loginUser()
        response = self.testapp.post('/suggest/event/video?event_key=2016necmp', {
            'num_videos': 1,
            'video_id_0': '37F5tbrFqJQ',
            'match_partial_0': 'f1m1'
        }).follow()
        self.assertEqual(response.status_int, 200)

        request = response.request
        self.assertEqual(request.GET.get('num_added'), '1')

        suggestion_id = "media_2016_match_2016necmp_f1m1_youtube_37F5tbrFqJQ"
        suggestion = Suggestion.get_by_id(suggestion_id)
        self.assertIsNotNone(suggestion)
