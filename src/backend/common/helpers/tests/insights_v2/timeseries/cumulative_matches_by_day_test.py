import datetime
import json
from typing import Optional

from google.appengine.ext import ndb

from backend.common.consts.comp_level import CompLevel
from backend.common.consts.event_type import EventType
from backend.common.helpers.insights_v2.registry import compute_insights_for_year
from backend.common.helpers.insights_v2.timeseries.cumulative_matches_by_day import (
    CumulativeMatchesByDayV2Calculator,
)
from backend.common.models.event import Event
from backend.common.models.insight_v2 import InsightCategory
from backend.common.models.match import Match

_ALL_TEAMS = ["frc1", "frc2", "frc3", "frc4", "frc5", "frc6"]


def _alliances_json(red_score: int, blue_score: int) -> str:
    return json.dumps(
        {
            "red": {"score": red_score, "teams": ["frc1", "frc2", "frc3"]},
            "blue": {"score": blue_score, "teams": ["frc4", "frc5", "frc6"]},
        }
    )


def _put_event(
    event_key: str,
    year: int,
    event_type: EventType = EventType.REGIONAL,
    start_date: Optional[datetime.datetime] = None,
    end_date: Optional[datetime.datetime] = None,
) -> None:
    Event(
        id=event_key,
        year=year,
        event_short=event_key[4:],
        event_type_enum=event_type,
        start_date=start_date,
        end_date=end_date,
    ).put()


def _put_match(
    event_key: str,
    year: int,
    match_number: int,
    post_result_time: Optional[datetime.datetime],
    comp_level: CompLevel = CompLevel.QM,
    red_score: int = 10,
    blue_score: int = 5,
) -> None:
    Match(
        id=f"{event_key}_{comp_level.value}{match_number}",
        comp_level=comp_level,
        event=ndb.Key(Event, event_key),
        year=year,
        match_number=match_number,
        set_number=1,
        team_key_names=_ALL_TEAMS,
        alliances_json=_alliances_json(red_score, blue_score),
        post_result_time=post_result_time,
    ).put()


def _calc() -> CumulativeMatchesByDayV2Calculator:
    return CumulativeMatchesByDayV2Calculator()


def _epoch(y: int, m: int, d: int) -> int:
    return (datetime.date(y, m, d) - datetime.date(1970, 1, 1)).days * 86400


def test_cumulative_count_across_days(ndb_stub) -> None:
    _put_event("2024nyny", 2024)
    _put_match("2024nyny", 2024, 1, datetime.datetime(2024, 3, 1, 10))
    _put_match("2024nyny", 2024, 2, datetime.datetime(2024, 3, 1, 12))
    _put_match("2024nyny", 2024, 3, datetime.datetime(2024, 3, 3, 9))

    insights = compute_insights_for_year(2024, [_calc()])

    assert len(insights) == 1
    insight = insights[0]
    assert insight.name == "cumulative_matches_by_day"
    assert insight.display_name == "Matches over Time"
    assert insight.category == InsightCategory.TIMESERIES
    assert insight.year == 2024
    assert insight.key_name == "2024_v2_timeseries_cumulative_matches_by_day"

    data = insight.data
    assert data["x_type"] == "date"
    assert data["point_context_type"] == "none"
    assert len(data["series"]) == 1

    points = data["series"][0]["points"]
    assert points == [
        {"x": _epoch(2024, 3, 1), "y": 2.0},
        {"x": _epoch(2024, 3, 2), "y": 2.0},
        {"x": _epoch(2024, 3, 3), "y": 3.0},
    ]


def test_falls_back_to_event_dates_without_timestamps(ndb_stub) -> None:
    _put_event(
        "2024nyny",
        2024,
        start_date=datetime.datetime(2024, 3, 10),
        end_date=datetime.datetime(2024, 3, 12),
    )
    _put_match("2024nyny", 2024, 1, None, comp_level=CompLevel.QM)
    _put_match("2024nyny", 2024, 1, None, comp_level=CompLevel.F)

    insights = compute_insights_for_year(2024, [_calc()])

    points = insights[0].data["series"][0]["points"]
    assert points[0] == {"x": _epoch(2024, 3, 10), "y": 1.0}
    assert points[-1] == {"x": _epoch(2024, 3, 12), "y": 2.0}


def test_unplayed_matches_not_counted(ndb_stub) -> None:
    _put_event("2024nyny", 2024)
    _put_match("2024nyny", 2024, 1, datetime.datetime(2024, 3, 1))
    _put_match(
        "2024nyny", 2024, 2, datetime.datetime(2024, 3, 2), red_score=-1, blue_score=-1
    )

    insights = compute_insights_for_year(2024, [_calc()])

    assert insights[0].data["series"][0]["points"] == [
        {"x": _epoch(2024, 3, 1), "y": 1.0}
    ]


def test_no_played_matches_produces_no_insight(ndb_stub) -> None:
    _put_event("2024nyny", 2024)
    _put_match(
        "2024nyny", 2024, 1, datetime.datetime(2024, 3, 1), red_score=-1, blue_score=-1
    )

    insights = compute_insights_for_year(2024, [_calc()])

    assert insights == []
