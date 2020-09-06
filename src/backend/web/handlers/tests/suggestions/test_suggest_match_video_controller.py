from datetime import datetime
from typing import cast, List
from urllib.parse import urlparse

import pytest
from bs4 import BeautifulSoup
from google.cloud import ndb
from werkzeug.test import Client

from backend.common.consts.event_type import EventType
from backend.common.consts.suggestion_state import SuggestionState
from backend.common.models.event import Event
from backend.common.models.match import Match
from backend.common.models.suggestion import Suggestion
from backend.common.models.suggestion_dict import SuggestionDict
from backend.web.handlers.tests.conftest import CapturedTemplate


@pytest.fixture(autouse=True)
def createMatchAndEvent(ndb_client: ndb.Client):
    with ndb_client.context():
        event = Event(
            id="2016necmp",
            name="New England District Championship",
            event_type_enum=EventType.DISTRICT_CMP,
            short_name="New England",
            event_short="necmp",
            year=2016,
            end_date=datetime(2016, 3, 27),
            official=False,
            city="Hartford",
            state_prov="CT",
            country="USA",
            venue="Some Venue",
            venue_address="Some Venue, Hartford, CT, USA",
            timezone_id="America/New_York",
            start_date=datetime(2016, 3, 24),
            webcast_json="",
            website="http://www.firstsv.org",
        )
        event.put()

        match = Match(
            id="2016necmp_f1m1",
            event=ndb.Key(Event, "2016necmp"),
            year=2016,
            comp_level="f",
            set_number=1,
            match_number=1,
            team_key_names=[
                "frc846",
                "frc2135",
                "frc971",
                "frc254",
                "frc1678",
                "frc973",
            ],
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
                    "truss+catch": 40}}',
        )
        match.put()


def assert_template_status(
    captured_templates: List[CapturedTemplate], status: str
) -> None:
    template = captured_templates[0][0]
    context = captured_templates[0][1]
    assert template.name == "suggestions/suggest_match_video.html"
    assert context["status"] == status


def test_login_redirect(web_client: Client) -> None:
    response = web_client.get("/suggest/match/video?match_key=2016necmp_f1m1")
    assert response.status_code == 302
    assert urlparse(response.headers["Location"]).path == "/account/login"


def test_bad_match(login_user, web_client: Client) -> None:
    response = web_client.get("/suggest/match/video?match_key=2016necmp_f1m2")
    assert response.status_code == 404


def test_get_form(login_user, web_client: Client) -> None:
    response = web_client.get("/suggest/match/video?match_key=2016necmp_f1m1")
    assert response.status_code == 200

    soup = BeautifulSoup(response.data, "html.parser")
    form = soup.find("form", id="suggest_match_video")
    assert form is not None
    assert form["action"] == "/suggest/match/video"
    assert form["method"] == "post"

    csrf = form.find(attrs={"name": "csrf_token"})
    assert csrf is not None
    assert csrf["type"] == "hidden"
    assert csrf["value"] is not None

    match_key = form.find(attrs={"name": "match_key"})
    assert match_key is not None
    assert match_key["type"] == "hidden"
    assert match_key["value"] == "2016necmp_f1m1"

    assert form.find(attrs={"name": "youtube_url"}) is not None


def test_submit_no_match(
    login_user,
    ndb_client: ndb.Client,
    web_client: Client,
) -> None:
    resp = web_client.post("/suggest/match/video", data={}, follow_redirects=True)
    assert resp.status_code == 404

    # Assert no suggestions were written
    with ndb_client.context():
        assert Suggestion.query().fetch() == []


def test_submit_empty_form(
    login_user,
    ndb_client: ndb.Client,
    web_client: Client,
    captured_templates: List[CapturedTemplate],
) -> None:
    resp = web_client.post(
        "/suggest/match/video",
        data={"match_key": "2016necmp_f1m1"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert_template_status(captured_templates, "invalid_url")

    # Assert the correct dialog shows
    soup = BeautifulSoup(resp.data, "html.parser")
    assert soup.find(id="invalid_url-alert") is not None

    # Assert no suggestions were written
    with ndb_client.context():
        assert Suggestion.query().fetch() == []


def test_submit_bad_url(
    login_user,
    ndb_client: ndb.Client,
    web_client: Client,
    captured_templates: List[CapturedTemplate],
) -> None:
    resp = web_client.post(
        "/suggest/match/video",
        data={"match_key": "2016necmp_f1m1", "youtube_url": "asdf"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert_template_status(captured_templates, "invalid_url")

    # Assert the correct dialog shows
    soup = BeautifulSoup(resp.data, "html.parser")
    assert soup.find(id="invalid_url-alert") is not None

    # Assert no suggestions were written
    with ndb_client.context():
        assert Suggestion.query().fetch() == []


def test_submit_match_video(
    login_user,
    ndb_client: ndb.Client,
    web_client: Client,
    captured_templates: List[CapturedTemplate],
) -> None:
    resp = web_client.post(
        "/suggest/match/video",
        data={
            "match_key": "2016necmp_f1m1",
            "youtube_url": "http://youtu.be/bHGyTjxbLz8",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert_template_status(captured_templates, "success")

    # Assert the correct dialog shows
    soup = BeautifulSoup(resp.data, "html.parser")
    assert soup.find(id="success-alert") is not None

    # Make sure the Suggestion gets created
    with ndb_client.context():
        suggestion = cast(Suggestion, Suggestion.query().fetch()[0])
        assert suggestion is not None
        assert suggestion.review_state == SuggestionState.REVIEW_PENDING
        assert suggestion.target_key == "2016necmp_f1m1"
        assert suggestion.contents == SuggestionDict(youtube_videos=["bHGyTjxbLz8"])


"""
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
"""
