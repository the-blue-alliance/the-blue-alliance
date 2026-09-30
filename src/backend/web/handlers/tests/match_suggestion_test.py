import json
import math
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from unittest.mock import patch
from urllib.parse import parse_qsl, urlparse

import pytest
from flask.testing import FlaskClient
from google.appengine.ext import ndb

from backend.common.consts.award_type import AwardType
from backend.common.consts.comp_level import CompLevel
from backend.common.consts.event_type import EventType
from backend.common.consts.model_type import ModelType
from backend.common.helpers.mytba_helper import MyTBAHelper
from backend.common.memcache import MemcacheClient
from backend.common.models.award import Award
from backend.common.models.event import Event
from backend.common.models.event_details import EventDetails
from backend.common.models.event_team import EventTeam
from backend.common.models.favorite import Favorite
from backend.common.models.match import Match
from backend.common.models.team import Team
from backend.web.handlers.conftest import CapturedTemplate
from backend.web.handlers.match_suggestion import (
    fetch_team_details_async,
    get_qual_bluezone_score,
)

YEAR = datetime.now().year

QM2_PREDICTION = {
    "red": {"score": 120.0, "note_scored": 25.0, "stage_points": 12.0},
    "blue": {"score": 80.0, "note_scored": 15.0, "stage_points": 6.0},
}


def _put_event(
    event_short: str,
    start: datetime,
    end: datetime,
    event_type: EventType = EventType.REGIONAL,
) -> Event:
    event = Event(
        id=f"{YEAR}{event_short}",
        year=YEAR,
        event_short=event_short,
        name=f"Event {event_short}",
        event_type_enum=event_type,
        start_date=start,
        end_date=end,
    )
    event.put()
    return event


def _put_match(
    event_key: str,
    match_number: int,
    red: List[str],
    blue: List[str],
    red_score: int = -1,
    blue_score: int = -1,
    time: Optional[datetime] = None,
    actual_time: Optional[datetime] = None,
) -> Match:
    match = Match(
        id=f"{event_key}_qm{match_number}",
        event=ndb.Key(Event, event_key),
        year=YEAR,
        comp_level=CompLevel.QM,
        set_number=1,
        match_number=match_number,
        alliances_json=json.dumps(
            {
                "red": {"teams": red, "score": red_score},
                "blue": {"teams": blue, "score": blue_score},
            }
        ),
        team_key_names=red + blue,
        time=time,
        actual_time=actual_time,
    )
    match.put()
    return match


def _put_event_team(
    event_key: str, team_number: int, status: Optional[Dict[str, Any]] = None
) -> None:
    EventTeam(
        id=f"{event_key}_frc{team_number}",
        event=ndb.Key(Event, event_key),
        team=ndb.Key(Team, f"frc{team_number}"),
        year=YEAR,
        status=status,
    ).put()


@pytest.fixture
def teams(ndb_stub) -> None:
    for team_number in range(1, 9):
        Team(
            id=f"frc{team_number}",
            team_number=team_number,
            nickname=f"Team {team_number}",
        ).put()


@pytest.fixture
def live_event(teams) -> Event:
    """A currently-running event with details, predictions and matches."""
    now = datetime.now()
    event = _put_event("live", now - timedelta(days=1), now + timedelta(days=1))
    event_key = event.key_name

    EventDetails(
        id=event_key,
        predictions={
            "match_predictions": {
                "qual": {f"{event_key}_qm2": QM2_PREDICTION},
                "playoff": {},
            }
        },
        rankings2=[
            {"team_key": "frc1", "rank": 1},
            {"team_key": "frc4", "rank": 2},
        ],
        alliance_selections=[
            {"picks": ["frc1", "frc2", "frc3"]},
            {"picks": ["frc4", "frc5", "frc6"]},
        ],
    ).put()

    # qm1 has been played; qm2 (predicted) and qm3 (unpredicted) are upcoming;
    # qm4 has no scheduled time and is skipped
    _put_match(
        event_key,
        1,
        ["frc1", "frc2", "frc3"],
        ["frc4", "frc5", "frc6"],
        red_score=50,
        blue_score=40,
        time=now - timedelta(hours=2),
        actual_time=now - timedelta(hours=1, minutes=50),
    )
    _put_match(
        event_key,
        2,
        ["frc1", "frc2", "frc7"],
        ["frc4", "frc5", "frc8"],
        time=now + timedelta(hours=1),
    )
    _put_match(
        event_key,
        3,
        ["frc3", "frc6", "frc7"],
        ["frc1", "frc4", "frc8"],
        time=now + timedelta(hours=2),
    )
    _put_match(event_key, 4, ["frc2", "frc5", "frc8"], ["frc3", "frc6", "frc7"])

    # frc1 is registered at the live event, and is somebody's favorite, so it
    # shows up as a popular team
    _put_event_team(event_key, 1)
    return event


@pytest.fixture
def popular_frc1(login_user, live_event: Event) -> None:
    MyTBAHelper.add_favorite(
        Favorite(
            parent=login_user.account_key,
            user_id=str(login_user.account_key.id()),
            model_type=ModelType.TEAM,
            model_key="frc1",
        )
    )


@pytest.fixture
def frc1_history(teams) -> Event:
    """Season history for frc1 that feeds the team detail popover."""
    now = datetime.now()

    # A completed event with cOPRs and a playoff result
    past = _put_event("past", now - timedelta(days=30), now - timedelta(days=28))
    EventDetails(
        id=past.key_name,
        coprs={
            "Total Auto Game Pieces": {"1": 3.5},
            "Total Teleop Game Pieces": {"1": 10.25},
            "Total Trap": {"1": 0.5},
        },
    ).put()
    _put_event_team(
        past.key_name,
        1,
        status={
            "qual": None,
            "alliance": {"number": 2, "pick": 0, "name": None, "backup": None},
            "playoff": {
                "level": "f",
                "status": "won",
                "double_elim_round": "Finals",
                "record": None,
                "current_level_record": None,
            },
            "last_match_key": None,
            "next_match_key": None,
        },
    )

    # A completed event with no EventDetails is skipped
    no_details = _put_event(
        "nodetails", now - timedelta(days=20), now - timedelta(days=18)
    )
    _put_event_team(no_details.key_name, 1)

    # An EventTeam whose Event has been deleted is skipped (and logged)
    _put_event_team(f"{YEAR}ghost", 1)

    # A division win this year means a past Einstein appearance
    division = _put_event(
        "arc",
        now - timedelta(days=10),
        now - timedelta(days=8),
        event_type=EventType.CMP_DIVISION,
    )
    Award(
        id=f"{division.key_name}_{int(AwardType.WINNER)}",
        name_str="Division Winner",
        award_type_enum=AwardType.WINNER,
        year=YEAR,
        event=division.key,
        event_type_enum=EventType.CMP_DIVISION,
        team_list=[ndb.Key(Team, "frc1")],
        recipient_json_list=[json.dumps({"team_number": 1, "awardee": None})],
    ).put()

    return past


def test_get_qual_bluezone_score() -> None:
    score = get_qual_bluezone_score(QM2_PREDICTION)
    # Score power: (120 + 2 * 80) / 600 * 50; skill power: capped note and
    # stage contributions averaged over 4 and scaled to 50
    expected_score_power = (120 + 2 * 80) / 600 * 50
    expected_skill_power = (1 + 15 / 21 + 1 + 6 / 10) * 50 / 4
    assert math.isclose(score, expected_score_power + expected_skill_power)

    # Symmetric: swapping alliances doesn't change the score
    swapped = {"red": QM2_PREDICTION["blue"], "blue": QM2_PREDICTION["red"]}
    assert math.isclose(get_qual_bluezone_score(swapped), score)

    # Both powers are capped at 50
    blowout = {
        "red": {"score": 500.0, "note_scored": 100.0, "stage_points": 100.0},
        "blue": {"score": 400.0, "note_scored": 100.0, "stage_points": 100.0},
    }
    assert get_qual_bluezone_score(blowout) == 100


def test_match_suggestion_logged_out(web_client: FlaskClient) -> None:
    response = web_client.get("/match_suggestion")

    assert response.status_code == 302
    parsed_response = urlparse(response.headers["Location"])
    assert parsed_response.path == "/account/login"
    assert dict(parse_qsl(parsed_response.query)) == {
        "next": "http://localhost/match_suggestion"
    }


def test_match_suggestion_no_live_events(
    login_user, captured_templates: List[CapturedTemplate], web_client: FlaskClient
) -> None:
    response = web_client.get("/match_suggestion")

    assert response.status_code == 200
    template, context = captured_templates[0]
    assert template.name == "match_suggestion.html"
    assert context["finished_matches"] == []
    assert context["current_matches"] == []
    assert context["upcoming_matches"] == []
    assert context["ranks"] == {}
    assert context["alliances"] == {}
    assert context["popular_team_keys"] == set()
    assert context["team_details"] == {}


def test_match_suggestion_skips_live_events_without_details(
    login_user,
    teams,
    captured_templates: List[CapturedTemplate],
    web_client: FlaskClient,
) -> None:
    now = datetime.now()
    event = _put_event("bare", now - timedelta(days=1), now + timedelta(days=1))
    _put_match(event.key_name, 1, ["frc1", "frc2", "frc3"], ["frc4", "frc5", "frc6"])

    response = web_client.get("/match_suggestion")

    assert response.status_code == 200
    context = captured_templates[0][1]
    assert context["current_matches"] == []
    assert context["upcoming_matches"] == []
    assert context["team_details"] == {}


def test_match_suggestion_live_event(
    login_user,
    live_event: Event,
    popular_frc1,
    frc1_history: Event,
    captured_templates: List[CapturedTemplate],
    web_client: FlaskClient,
) -> None:
    event_key = live_event.key_name

    response = web_client.get("/match_suggestion")

    assert response.status_code == 200
    template, context = captured_templates[0]
    assert template.name == "match_suggestion.html"

    assert [m.key_name for m in context["finished_matches"]] == [f"{event_key}_qm1"]

    # The first upcoming match is "current"; the rest are "upcoming". qm4 has
    # no scheduled time and is dropped entirely.
    current_matches = context["current_matches"]
    upcoming_matches = context["upcoming_matches"]
    assert [m.key_name for m in current_matches] == [f"{event_key}_qm2"]
    assert [m.key_name for m in upcoming_matches] == [f"{event_key}_qm3"]

    # qm2 has a prediction; qm3 falls back to zeros
    assert current_matches[0].prediction == QM2_PREDICTION
    assert math.isclose(
        current_matches[0].bluezone_score, get_qual_bluezone_score(QM2_PREDICTION)
    )
    assert upcoming_matches[0].bluezone_score == 0
    assert upcoming_matches[0].prediction["red"]["score"] == 0.0

    assert context["ranks"] == {"frc1": 1, "frc4": 2}
    assert context["alliances"] == {
        "frc1": 1,
        "frc2": 1,
        "frc3": 1,
        "frc4": 2,
        "frc5": 2,
        "frc6": 2,
    }
    assert context["popular_team_keys"] == {"frc1"}

    # Details are fetched for every team in a current or upcoming match
    team_details = context["team_details"]
    assert set(team_details.keys()) == {f"frc{n}" for n in range(1, 9)}

    frc1 = team_details["frc1"]
    assert frc1["team"].key.id() == "frc1"
    assert frc1["past_einstein"] == [YEAR]
    # Only the completed event with details is listed; the live event, the
    # event without details and the missing event are all skipped
    assert [e["event_short"] for e in frc1["events"]] == ["past"]
    past_details = frc1["events"][0]
    assert past_details["name"] == frc1_history.name
    assert past_details["alliance"] == "A2PC"
    assert past_details["finish"] == "Finals (won)"
    assert past_details["auto_note_copr"] == 3.5
    assert past_details["teleop_note_copr"] == 10.25
    assert past_details["trap_copr"] == 0.5

    # A team with no season history renders with empty details
    frc8 = team_details["frc8"]
    assert frc8["past_einstein"] == []
    assert frc8["events"] == []

    body = response.get_data(as_text=True)
    assert f"{event_key}_qm2" in body
    assert "Team 1" in body


def test_fetch_team_details_async_uses_memcache(
    login_user, frc1_history: Event
) -> None:
    from backend.web.main import app

    with app.test_request_context("/match_suggestion"):
        first = fetch_team_details_async("frc1").get_result()
        assert first["team"].key.id() == "frc1"
        assert [e["event_short"] for e in first["events"]] == ["past"]

        cached = MemcacheClient.get().get(b"match_suggestion_fetch_team_detailsfrc1")
        assert cached is not None
        assert cached["past_einstein"] == [YEAR]

        # A second call is served from memcache without touching the datastore
        with patch(
            "backend.web.handlers.match_suggestion.Team.get_by_id_async"
        ) as mock_get_by_id_async:
            second = fetch_team_details_async("frc1").get_result()

        mock_get_by_id_async.assert_not_called()
        assert second["team"].key.id() == "frc1"
        assert [e["event_short"] for e in second["events"]] == ["past"]
