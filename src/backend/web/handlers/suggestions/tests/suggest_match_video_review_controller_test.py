import re
from datetime import datetime
from typing import List
from urllib.parse import urlparse

import pytest
from bs4 import BeautifulSoup
from google.cloud import ndb
from werkzeug.test import Client

from backend.common.consts.account_permission import AccountPermission
from backend.common.consts.event_type import EventType
from backend.common.consts.suggestion_state import SuggestionState
from backend.common.models.event import Event
from backend.common.models.match import Match
from backend.common.models.suggestion import Suggestion
from backend.common.suggestions.suggestion_creator import (
    SuggestionCreationStatus,
    SuggestionCreator,
)


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

        match2 = Match(
            id="2016necmp_f1m2",
            event=ndb.Key(Event, "2016necmp"),
            year=2016,
            comp_level="f",
            set_number=1,
            match_number=2,
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
        match2.put()


@pytest.fixture
def login_user_with_permission(login_user):
    login_user.permissions = [AccountPermission.REVIEW_MEDIA]
    return login_user


def get_suggestion_queue(web_client: Client) -> List[str]:
    response = web_client.get("/suggest/match/video/review")
    assert response.status_code == 200
    soup = BeautifulSoup(response.data, "html.parser")
    review_form = soup.find(id="review_videos")
    assert review_form is not None
    suggestions = review_form.find_all(class_="suggestion-item")
    queue = []
    for suggestion in suggestions:
        accept_button = suggestion.find(
            "input",
            attrs={
                "name": re.compile("accept_reject-.*"),
                "value": re.compile("accept::.*"),
            },
        )
        assert accept_button is not None
        reject_button = suggestion.find(
            "input",
            attrs={
                "name": re.compile("accept_reject-.*"),
                "value": re.compile("reject::.*"),
            },
        )
        assert reject_button is not None
        match_key = suggestion.find("input", attrs={"name": re.compile("key-.*")})
        assert match_key is not None
        queue.append(accept_button["value"].split("::")[1])
    return queue


def createSuggestion(logged_in_user, ndb_client: ndb.Client) -> str:
    with ndb_client.context():
        status = SuggestionCreator.createMatchVideoYouTubeSuggestion(
            logged_in_user.account_key, "H-54KMwMKY0", "2016necmp_f1m1"
        )
        assert status == SuggestionCreationStatus.SUCCESS
        return Suggestion.render_media_key_name(
            2016, "match", "2016necmp_f1m1", "youtube", "H-54KMwMKY0"
        )


def test_login_redirect(web_client: Client) -> None:
    response = web_client.get("/suggest/match/video/review")
    assert response.status_code == 302
    assert urlparse(response.headers["Location"]).path == "/account/login"


def test_no_permissions(login_user, web_client: Client) -> None:
    response = web_client.get("/suggest/match/video/review")
    assert response.status_code == 401


def test_nothing_to_review(login_user_with_permission, web_client: Client) -> None:
    queue = get_suggestion_queue(web_client)
    assert queue == []


def test_accept_suggestion(
    login_user_with_permission,
    ndb_client: ndb.Client,
    web_client: Client,
    taskqueue_stub,
) -> None:
    suggestion_id = createSuggestion(login_user_with_permission, ndb_client)
    queue = get_suggestion_queue(web_client)
    assert queue == [suggestion_id]

    response = web_client.post(
        "/suggest/match/video/review",
        data={
            f"accept_reject-{suggestion_id}": f"accept::{suggestion_id}",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200

    # Make sure we mark the Suggestion as REVIEWED
    with ndb_client.context():
        suggestion = Suggestion.get_by_id(suggestion_id)
        assert suggestion is not None
        assert suggestion.review_state == SuggestionState.REVIEW_ACCEPTED

        # Make sure the video gets associated
        match = Match.get_by_id("2016necmp_f1m1")
        assert match is not None
        assert match.youtube_videos is not None
        assert "H-54KMwMKY0" in match.youtube_videos


def test_accept_new_key(
    login_user_with_permission,
    ndb_client: ndb.Client,
    web_client: Client,
    taskqueue_stub,
) -> None:
    suggestion_id = createSuggestion(login_user_with_permission, ndb_client)
    queue = get_suggestion_queue(web_client)
    assert queue == [suggestion_id]

    response = web_client.post(
        "/suggest/match/video/review",
        data={
            f"accept_reject-{suggestion_id}": f"accept::{suggestion_id}",
            f"key-{suggestion_id}": "2016necmp_f1m2",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200

    with ndb_client.context():
        # Make sure we mark the Suggestion as REVIEWED
        suggestion = Suggestion.get_by_id(suggestion_id)
        assert suggestion is not None
        assert suggestion.review_state == SuggestionState.REVIEW_ACCEPTED

        # Make sure the video gets associated
        match = Match.get_by_id("2016necmp_f1m2")
        assert match is not None
        assert match.youtube_videos is not None
        assert "H-54KMwMKY0" in match.youtube_videos

        # Make sure we don't add it to the first match
        match = Match.get_by_id("2016necmp_f1m1")
        assert match is not None
        assert match.youtube_videos is not None
        assert "H-54KMwMKY0" not in match.youtube_videos


def test_accept_bad_key(
    login_user_with_permission, ndb_client: ndb.Client, web_client: Client
) -> None:
    suggestion_id = createSuggestion(login_user_with_permission, ndb_client)
    queue = get_suggestion_queue(web_client)
    assert queue == [suggestion_id]

    response = web_client.post(
        "/suggest/match/video/review",
        data={
            f"accept_reject-{suggestion_id}": f"accept::{suggestion_id}",
            f"key-{suggestion_id}": "2016necmp_f1m3",  # this match doesn't exist
        },
        follow_redirects=True,
    )
    assert response.status_code == 200

    with ndb_client.context():
        # Make sure we don't mark the Suggestion as REVIEWED
        suggestion = Suggestion.get_by_id(suggestion_id)
        assert suggestion is not None
        assert suggestion.review_state == SuggestionState.REVIEW_PENDING

        # Make sure the video doesn't get associated
        match = Match.get_by_id("2016necmp_f1m1")
        assert match is not None
        assert match.youtube_videos is not None
        assert "H-54KMwMKY0" not in match.youtube_videos


def test_reject_suggestion(
    login_user_with_permission, ndb_client: ndb.Client, web_client: Client
) -> None:
    suggestion_id = createSuggestion(login_user_with_permission, ndb_client)
    queue = get_suggestion_queue(web_client)
    assert queue == [suggestion_id]

    response = web_client.post(
        "/suggest/match/video/review",
        data={
            f"accept_reject-{suggestion_id}": f"reject::{suggestion_id}",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200

    with ndb_client.context():
        # Make sure we mark the Suggestion as REVIEWED
        suggestion = Suggestion.get_by_id(suggestion_id)
        assert suggestion is not None
        assert suggestion.review_state == SuggestionState.REVIEW_REJECTED

        # Make sure the video gets associated
        match = Match.get_by_id("2016necmp_f1m1")
        assert match is not None
        assert "H-54KMwMKY0" not in match.youtube_videos
