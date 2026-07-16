import datetime
import json

from google.appengine.ext import ndb

from backend.common.consts.comp_level import CompLevel
from backend.common.consts.event_type import EventType
from backend.common.helpers.insights_v2.registry import compute_insights_for_year
from backend.common.helpers.insights_v2.timeseries.average_match_score_by_week import (
    AverageMatchScoreByWeekV2Calculator,
)
from backend.common.models.event import Event
from backend.common.models.insight_v2 import InsightCategory
from backend.common.models.match import Match

_WEEK_1_START = datetime.datetime(2022, 1, 3)
_WEEK_2_START = datetime.datetime(2022, 1, 10)


def _alliances_json(red_score: int, blue_score: int) -> str:
    return json.dumps(
        {
            "red": {
                "score": red_score,
                "teams": ["frc1", "frc2", "frc3"],
                "surrogates": [],
                "dqs": [],
            },
            "blue": {
                "score": blue_score,
                "teams": ["frc4", "frc5", "frc6"],
                "surrogates": [],
                "dqs": [],
            },
        }
    )


def _put_event(
    event_key: str,
    year: int,
    event_type_enum: int = EventType.REGIONAL,
    start_date: datetime.datetime = _WEEK_1_START,
    official: bool = True,
) -> None:
    Event(
        id=event_key,
        year=year,
        event_short=event_key[4:],
        event_type_enum=event_type_enum,
        start_date=start_date,
        official=official,
    ).put()


def _put_match(
    event_key: str,
    year: int,
    match_number: int,
    red_score: int,
    blue_score: int,
    comp_level: CompLevel = CompLevel.QM,
) -> None:
    Match(
        id=f"{event_key}_{comp_level}{match_number if comp_level == CompLevel.QM else 'm' + str(match_number)}",
        comp_level=comp_level,
        event=ndb.Key(Event, event_key),
        year=year,
        match_number=match_number,
        set_number=1,
        team_key_names=["frc1", "frc2", "frc3", "frc4", "frc5", "frc6"],
        alliances_json=_alliances_json(red_score, blue_score),
    ).put()


def test_single_week_average(ndb_stub) -> None:
    _put_event("2022casj", 2022, start_date=_WEEK_1_START)
    _put_match("2022casj", 2022, 1, 100, 80)
    _put_match("2022casj", 2022, 2, 60, 40)

    insights = compute_insights_for_year(2022, [AverageMatchScoreByWeekV2Calculator()])

    assert len(insights) == 1
    insight = insights[0]
    assert insight.name == "match_averages_by_week"
    assert insight.category == InsightCategory.TIMESERIES
    assert insight.year == 2022

    points = insight.data["series"][0]["points"]
    assert len(points) == 1
    # (100 + 80 + 60 + 40) / 2 matches / 2 alliances = 70.0
    assert points[0]["x"] == 1
    assert points[0]["y"] == 70.0


def test_two_weeks_grouped_separately(ndb_stub) -> None:
    _put_event("2022casj", 2022, start_date=_WEEK_1_START)
    _put_match("2022casj", 2022, 1, 100, 80)

    _put_event("2022caln", 2022, start_date=_WEEK_2_START)
    _put_match("2022caln", 2022, 1, 60, 40)

    insights = compute_insights_for_year(2022, [AverageMatchScoreByWeekV2Calculator()])

    assert len(insights) == 1
    points = insights[0].data["series"][0]["points"]
    assert len(points) == 2
    assert points[0]["x"] == 1
    assert points[0]["y"] == 90.0  # (100 + 80) / 1 / 2
    assert points[1]["x"] == 2
    assert points[1]["y"] == 50.0  # (60 + 40) / 1 / 2


def test_elim_only_insight_uses_elim_matches_only(ndb_stub) -> None:
    _put_event("2022casj", 2022, start_date=_WEEK_1_START)
    _put_match("2022casj", 2022, 1, 100, 80, comp_level=CompLevel.QM)
    _put_match("2022casj", 2022, 1, 60, 40, comp_level=CompLevel.F)

    insights = compute_insights_for_year(2022, [AverageMatchScoreByWeekV2Calculator()])

    assert len(insights) == 2
    all_insight = next(i for i in insights if i.name == "match_averages_by_week")
    elim_insight = next(i for i in insights if i.name == "elim_match_averages_by_week")

    all_points = all_insight.data["series"][0]["points"]
    assert all_points[0]["y"] == 70.0  # (100 + 80 + 60 + 40) / 2 / 2

    elim_points = elim_insight.data["series"][0]["points"]
    assert len(elim_points) == 1
    assert elim_points[0]["y"] == 50.0  # (60 + 40) / 1 / 2


def test_no_elim_matches_produces_no_elim_insight(ndb_stub) -> None:
    _put_event("2022casj", 2022, start_date=_WEEK_1_START)
    _put_match("2022casj", 2022, 1, 100, 80, comp_level=CompLevel.QM)

    insights = compute_insights_for_year(2022, [AverageMatchScoreByWeekV2Calculator()])

    assert len(insights) == 1
    assert insights[0].name == "match_averages_by_week"


def test_unplayed_matches_skipped(ndb_stub) -> None:
    _put_event("2022casj", 2022, start_date=_WEEK_1_START)
    _put_match("2022casj", 2022, 1, -1, -1)

    insights = compute_insights_for_year(2022, [AverageMatchScoreByWeekV2Calculator()])

    assert insights == []


def test_offseason_event_skipped(ndb_stub) -> None:
    _put_event(
        "2022iri",
        2022,
        event_type_enum=EventType.OFFSEASON,
        start_date=_WEEK_1_START,
        official=False,
    )
    _put_match("2022iri", 2022, 1, 100, 80)

    insights = compute_insights_for_year(2022, [AverageMatchScoreByWeekV2Calculator()])

    assert insights == []


def test_championship_event_lands_on_trailing_week(ndb_stub) -> None:
    _put_event("2022casj", 2022, start_date=_WEEK_1_START)
    _put_match("2022casj", 2022, 1, 100, 80)

    _put_event(
        "2022cmptx",
        2022,
        event_type_enum=EventType.CMP_FINALS,
        start_date=datetime.datetime(2022, 4, 20),
    )
    _put_match("2022cmptx", 2022, 1, 200, 160)

    insights = compute_insights_for_year(2022, [AverageMatchScoreByWeekV2Calculator()])

    assert len(insights) == 1
    points = insights[0].data["series"][0]["points"]
    assert len(points) == 2
    assert points[0]["x"] == 1
    assert points[0]["y"] == 90.0
    # Championship has no numeric week, so it's placed one week after the
    # last regular week.
    assert points[1]["x"] == 2
    assert points[1]["y"] == 180.0


def test_no_matches_produces_no_insights(ndb_stub) -> None:
    _put_event("2022casj", 2022, start_date=_WEEK_1_START)

    insights = compute_insights_for_year(2022, [AverageMatchScoreByWeekV2Calculator()])

    assert insights == []


def test_key_name(ndb_stub) -> None:
    _put_event("2022casj", 2022, start_date=_WEEK_1_START)
    _put_match("2022casj", 2022, 1, 100, 80)

    insights = compute_insights_for_year(2022, [AverageMatchScoreByWeekV2Calculator()])

    assert len(insights) == 1
    assert insights[0].key_name == "2022_v2_timeseries_match_averages_by_week"
    assert insights[0].display_name == "Average Match Score By Week"
