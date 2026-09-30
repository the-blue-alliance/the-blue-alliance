import json
from datetime import datetime, timedelta
from typing import Any, Dict, List
from urllib.parse import parse_qsl, urlparse

import pytest
from flask.testing import FlaskClient
from google.appengine.ext import ndb

from backend.common.consts.award_type import AwardType
from backend.common.consts.event_type import EventType
from backend.common.consts.model_type import ModelType
from backend.common.helpers.mytba_helper import MyTBAHelper
from backend.common.helpers.season_helper import SeasonHelper
from backend.common.models.award import Award
from backend.common.models.event import Event
from backend.common.models.event_team import EventTeam
from backend.common.models.favorite import Favorite
from backend.common.models.team import Team
from backend.web.handlers.conftest import CapturedTemplate


def _put_event(event_key: str, year: int, start: datetime, end: datetime) -> Event:
    event = Event(
        id=event_key,
        year=year,
        event_short=event_key[4:],
        name=f"Event {event_key[4:]}",
        event_type_enum=EventType.REGIONAL,
        start_date=start,
        end_date=end,
    )
    event.put()
    return event


def _put_event_team(
    event_key: str, team_number: int, year: int, status: Dict[str, Any] | None = None
) -> None:
    EventTeam(
        id=f"{event_key}_frc{team_number}",
        event=ndb.Key(Event, event_key),
        team=ndb.Key(Team, f"frc{team_number}"),
        year=year,
        status=status,
    ).put()


@pytest.fixture
def season(ndb_stub) -> int:
    return SeasonHelper.get_current_season()


@pytest.fixture
def favorite_teams(login_user, ndb_stub) -> List[Team]:
    teams = []
    for team_number in [1114, 254, 9999]:
        team = Team(id=f"frc{team_number}", team_number=team_number)
        team.put()
        teams.append(team)
        MyTBAHelper.add_favorite(
            Favorite(
                parent=login_user.account_key,
                user_id=str(login_user.account_key.id()),
                model_type=ModelType.TEAM,
                model_key=f"frc{team_number}",
            )
        )
    return teams


@pytest.fixture
def season_events(season: int, favorite_teams: List[Team]) -> Dict[str, Event]:
    now = datetime.now()
    past = _put_event(
        f"{season}past", season, now - timedelta(days=30), now - timedelta(days=28)
    )
    live = _put_event(
        f"{season}live", season, now - timedelta(days=1), now + timedelta(days=1)
    )
    future = _put_event(
        f"{season}future", season, now + timedelta(days=30), now + timedelta(days=32)
    )

    # 254 competed at the past event and won; 9999 has no events at all
    _put_event_team(
        past.key_name,
        254,
        season,
        status={
            "qual": {
                "status": "completed",
                "num_teams": 40,
                "ranking": {
                    "rank": 1,
                    "matches_played": 10,
                    "dq": 0,
                    "record": {"wins": 9, "losses": 1, "ties": 0},
                    "qual_average": None,
                    "sort_orders": [2.0],
                    "team_key": "frc254",
                },
                "sort_order_info": None,
            },
            "playoff": None,
            "alliance": None,
            "last_match_key": None,
            "next_match_key": None,
        },
    )
    Award(
        id=f"{past.key_name}_{int(AwardType.WINNER)}",
        name_str="Regional Winner",
        award_type_enum=AwardType.WINNER,
        year=season,
        event=past.key,
        event_type_enum=EventType.REGIONAL,
        team_list=[ndb.Key(Team, "frc254")],
        recipient_json_list=[json.dumps({"team_number": 254, "awardee": None})],
    ).put()

    # Both 254 and 1114 are at the live and future events
    for team_number in [254, 1114]:
        _put_event_team(live.key_name, team_number, season)
        _put_event_team(future.key_name, team_number, season)

    return {"past": past, "live": live, "future": future}


def test_mytba_live_logged_out(web_client: FlaskClient) -> None:
    response = web_client.get("/mytba")

    assert response.status_code == 302
    parsed_response = urlparse(response.headers["Location"])
    assert parsed_response.path == "/account/login"
    assert dict(parse_qsl(parsed_response.query)) == {"next": "http://localhost/mytba"}


def test_mytba_live_no_favorites(
    login_user,
    season: int,
    captured_templates: List[CapturedTemplate],
    web_client: FlaskClient,
) -> None:
    response = web_client.get("/mytba")

    assert response.status_code == 200
    template, context = captured_templates[0]
    assert template.name == "mytba_live.html"
    assert context["year"] == season
    assert context["past_only"] is False
    assert context["past_events_with_teams"] == []
    assert context["live_events_with_teams"] == []
    assert context["future_events_with_teams"] == []


def test_mytba_live_buckets_favorite_team_events(
    login_user,
    season: int,
    season_events: Dict[str, Event],
    captured_templates: List[CapturedTemplate],
    web_client: FlaskClient,
) -> None:
    response = web_client.get("/mytba")

    assert response.status_code == 200
    context = captured_templates[0][1]
    assert context["year"] == season
    assert context["past_only"] is False

    # Past: only 254 competed, and it carries its status, strings and awards
    past_events = context["past_events_with_teams"]
    assert len(past_events) == 1
    past_event, past_teams = past_events[0]
    assert past_event.key == season_events["past"].key
    assert len(past_teams) == 1
    team, status, status_strings, awards = past_teams[0]
    assert team.team_number == 254
    assert status["qual"]["ranking"]["rank"] == 1
    assert set(status_strings.keys()) == {"alliance", "playoff", "overall"}
    assert [a.award_type_enum for a in awards] == [AwardType.WINNER]

    # Live: both favorites, sorted by team number
    live_events = context["live_events_with_teams"]
    assert len(live_events) == 1
    live_event, live_teams = live_events[0]
    assert live_event.key == season_events["live"].key
    assert [t.team_number for t, _, _, _ in live_teams] == [254, 1114]
    # No status recorded for the live EventTeams yet
    assert [status for _, status, _, _ in live_teams] == [None, None]
    assert [awards for _, _, _, awards in live_teams] == [[], []]

    # Future: teams only, sorted by team number
    future_events = context["future_events_with_teams"]
    assert len(future_events) == 1
    future_event, future_teams = future_events[0]
    assert future_event.key == season_events["future"].key
    assert [t.team_number for t in future_teams] == [254, 1114]

    body = response.get_data(as_text=True)
    assert "Regional Winner" in body


def test_mytba_live_past_year(
    login_user,
    season: int,
    season_events: Dict[str, Event],
    captured_templates: List[CapturedTemplate],
    web_client: FlaskClient,
) -> None:
    response = web_client.get(f"/mytba?year={season - 5}")

    assert response.status_code == 200
    context = captured_templates[0][1]
    assert context["year"] == season - 5
    assert context["past_only"] is True
    # The favorite teams have no events in that season
    assert context["past_events_with_teams"] == []
    assert context["live_events_with_teams"] == []
    assert context["future_events_with_teams"] == []


@pytest.mark.parametrize("year_param", ["abc", "", "20x4"])
def test_mytba_live_non_numeric_year_falls_back_to_current_season(
    login_user,
    season: int,
    year_param: str,
    captured_templates: List[CapturedTemplate],
    web_client: FlaskClient,
) -> None:
    response = web_client.get(f"/mytba?year={year_param}")

    assert response.status_code == 200
    context = captured_templates[0][1]
    assert context["year"] == season
    assert context["past_only"] is False
