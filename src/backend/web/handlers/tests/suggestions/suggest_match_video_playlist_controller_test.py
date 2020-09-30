import json
from datetime import datetime
from typing import cast, List
from unittest.mock import patch
from urllib.parse import urlparse

import pytest
from bs4 import BeautifulSoup
from google.cloud import ndb
from werkzeug.test import Client

from backend.common.consts.event_type import EventType
from backend.common.consts.suggestion_state import SuggestionState
from backend.common.helpers.youtube_video_helper import YouTubePlaylistItem
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


def assert_num_added(
    captured_templates: List[CapturedTemplate], num_added: int
) -> None:
    template = captured_templates[0][0]
    context = captured_templates[0][1]
    assert template.name == "suggestions/suggest_match_video_playlist.html"
    assert context["num_added"] == str(num_added)


def test_login_redirect(web_client: Client) -> None:
    response = web_client.get("/suggest/event/video?event_key=2016necmp")
    assert response.status_code == 302
    assert urlparse(response.headers["Location"]).path == "/account/login"


def test_garbage_event(login_user, web_client: Client) -> None:
    response = web_client.get("/suggest/event/video?event_key=asdf")
    assert response.status_code == 404


def test_bad_event(login_user, web_client: Client) -> None:
    response = web_client.get("/suggest/event/video?event_key=2016foo")
    assert response.status_code == 404


def test_get_form(login_user, web_client: Client) -> None:
    response = web_client.get("/suggest/event/video?event_key=2016necmp")
    assert response.status_code == 200

    soup = BeautifulSoup(response.data, "html.parser")
    form = soup.find("form", id="event_videos")
    assert form is not None
    assert form["action"] == "/suggest/event/video"
    assert form["method"] == "post"

    csrf = form.find(attrs={"name": "csrf_token"})
    assert csrf is not None
    assert csrf["type"] == "hidden"
    assert csrf["value"] is not None

    event_key = form.find(attrs={"name": "event_key"})
    assert event_key is not None
    assert event_key["type"] == "hidden"
    assert event_key["value"] == "2016necmp"


def test_submit_no_event(
    login_user, ndb_client: ndb.Client, web_client: Client
) -> None:
    resp = web_client.post(
        "/suggest/event/video",
        data={},
        follow_redirects=True,
    )
    assert resp.status_code == 404

    # Assert no suggestions were written
    with ndb_client.context():
        assert Suggestion.query().fetch() == []


def test_submit_bad_event(
    login_user, ndb_client: ndb.Client, web_client: Client
) -> None:
    resp = web_client.post(
        "/suggest/event/video",
        data={"event_key": "2016foo"},
        follow_redirects=True,
    )
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
        "/suggest/event/video",
        data={"event_key": "2016necmp"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert_num_added(captured_templates, 0)

    # Assert no suggestions were written
    with ndb_client.context():
        assert Suggestion.query().fetch() == []


def test_submit_partial_mismatch(
    login_user,
    ndb_client: ndb.Client,
    web_client: Client,
    captured_templates: List[CapturedTemplate],
) -> None:
    response = web_client.post(
        "/suggest/event/video?event_key=2016necmp",
        data={
            "event_key": "2016necmp",
            "num_videos": 1,
            "video_id_0": "37F5tbrFqJQ",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert_num_added(captured_templates, 0)

    # Assert no suggestions were written
    with ndb_client.context():
        assert Suggestion.query().fetch() == []


def test_submit_bad_match(
    login_user,
    ndb_client: ndb.Client,
    web_client: Client,
    captured_templates: List[CapturedTemplate],
) -> None:
    response = web_client.post(
        "/suggest/event/video?event_key=2016necmp",
        data={
            "event_key": "2016necmp",
            "num_videos": 1,
            "video_id_0": "37F5tbrFqJQ",
            "match_partial_0": "qm1",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert_num_added(captured_templates, 0)

    # Assert no suggestions were written
    with ndb_client.context():
        assert Suggestion.query().fetch() == []


def test_submit_one_video(
    login_user,
    ndb_client: ndb.Client,
    web_client: Client,
    captured_templates: List[CapturedTemplate],
) -> None:
    response = web_client.post(
        "/suggest/event/video?event_key=2016necmp",
        data={
            "event_key": "2016necmp",
            "num_videos": 1,
            "video_id_0": "37F5tbrFqJQ",
            "match_partial_0": "f1m1",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert_num_added(captured_templates, 1)

    with ndb_client.context():
        suggestions = Suggestion.query().fetch()
        assert len(suggestions) == 1
        suggestion = cast(Suggestion, suggestions[0])
        assert suggestion is not None
        assert suggestion.review_state == SuggestionState.REVIEW_PENDING
        assert suggestion.target_key == "2016necmp_f1m1"
        assert suggestion.contents == SuggestionDict(youtube_videos=["37F5tbrFqJQ"])


def test_ajax_no_login(web_client: Client) -> None:
    response = web_client.get("/suggest/_/yt/playlist/videos")
    assert response.status_code == 401


def test_ajax_no_playlist(login_user, web_client: Client) -> None:
    response = web_client.get("/suggest/_/yt/playlist/videos")
    assert response.status_code == 400


def test_ajax_resolve_playlist(login_user, web_client: Client) -> None:
    expected = [
        YouTubePlaylistItem(
            video_title="Video Title",
            video_id="abc123",
            guessed_match_partial="qm1",
        ),
    ]

    with patch(
        "backend.common.helpers.youtube_video_helper.YouTubeVideoHelper.videos_in_playlist"
    ) as playlist_mock:
        playlist_mock.return_value = expected

        resp = web_client.get("/suggest/_/yt/playlist/videos?playlist_id=plist1234")
        assert resp.status_code == 200
        assert json.loads(resp.data) == expected
        playlist_mock.assert_called_with("plist1234")
