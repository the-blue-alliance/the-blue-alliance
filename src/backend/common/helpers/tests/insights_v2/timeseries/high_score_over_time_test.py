import datetime
import json

from google.appengine.ext import ndb

from backend.common.consts.comp_level import CompLevel
from backend.common.consts.event_type import EventType
from backend.common.helpers.insights_v2.registry import compute_insights_for_year
from backend.common.helpers.insights_v2.timeseries.high_score_over_time import (
    HighScoreOverTimeV2Calculator,
)
from backend.common.models.event import Event
from backend.common.models.match import Match


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


def _put_event(event_key: str, year: int) -> None:
    Event(
        id=event_key,
        year=year,
        event_short=event_key[4:],
        event_type_enum=EventType.REGIONAL,
    ).put()


def _put_match(
    event_key: str,
    year: int,
    match_number: int,
    red_score: int,
    blue_score: int,
    post_result_time: datetime.datetime,
    red_foul_points: int = 0,
    blue_foul_points: int = 0,
) -> None:
    score_breakdown_json = None
    if red_foul_points or blue_foul_points:
        score_breakdown_json = json.dumps(
            {
                "red": {"foulPoints": red_foul_points},
                "blue": {"foulPoints": blue_foul_points},
            }
        )
    Match(
        id=f"{event_key}_qm{match_number}",
        comp_level=CompLevel.QM,
        event=ndb.Key(Event, event_key),
        year=year,
        match_number=match_number,
        set_number=1,
        team_key_names=["frc1", "frc2", "frc3", "frc4", "frc5", "frc6"],
        alliances_json=_alliances_json(red_score, blue_score),
        score_breakdown_json=score_breakdown_json,
        post_result_time=post_result_time,
    ).put()


def test_single_match_sets_initial_record(ndb_stub) -> None:
    _put_event("2022casj", 2022)
    _put_match("2022casj", 2022, 1, 100, 80, datetime.datetime(2022, 3, 5))

    insights = compute_insights_for_year(2022, [HighScoreOverTimeV2Calculator()])

    assert len(insights) == 1
    data = insights[0].data
    assert data["point_context_type"] == "match_record"
    assert data["x_type"] == "year"
    assert len(data["series"]) == 1
    series = data["series"][0]
    assert series["label"] == "World Record"
    assert len(series["points"]) == 1

    pt = series["points"][0]
    assert pt["x"] == 2022
    assert pt["y"] == 100.0
    assert pt["context"]["match_key"] == "2022casj_qm1"
    assert pt["context"]["alliance"] == ["frc1", "frc2", "frc3"]
    assert pt["context"]["is_current"] is True


def test_higher_score_breaks_record(ndb_stub) -> None:
    _put_event("2022casj", 2022)
    _put_match("2022casj", 2022, 1, 100, 80, datetime.datetime(2022, 3, 5))
    _put_match("2022casj", 2022, 2, 120, 90, datetime.datetime(2022, 3, 6))

    insights = compute_insights_for_year(2022, [HighScoreOverTimeV2Calculator()])

    assert len(insights) == 1
    points = insights[0].data["series"][0]["points"]
    assert len(points) == 2
    assert points[0]["y"] == 100.0
    assert points[0]["context"]["is_current"] is False
    assert points[1]["y"] == 120.0
    assert points[1]["context"]["is_current"] is True


def test_lower_score_does_not_break_record(ndb_stub) -> None:
    _put_event("2022casj", 2022)
    _put_match("2022casj", 2022, 1, 100, 80, datetime.datetime(2022, 3, 5))
    _put_match("2022casj", 2022, 2, 90, 70, datetime.datetime(2022, 3, 6))

    insights = compute_insights_for_year(2022, [HighScoreOverTimeV2Calculator()])

    assert len(insights) == 1
    points = insights[0].data["series"][0]["points"]
    assert len(points) == 1
    assert points[0]["y"] == 100.0


def test_equal_score_does_not_break_record(ndb_stub) -> None:
    _put_event("2022casj", 2022)
    _put_match("2022casj", 2022, 1, 100, 80, datetime.datetime(2022, 3, 5))
    _put_match("2022casj", 2022, 2, 100, 95, datetime.datetime(2022, 3, 6))

    insights = compute_insights_for_year(2022, [HighScoreOverTimeV2Calculator()])

    assert len(insights) == 1
    points = insights[0].data["series"][0]["points"]
    assert len(points) == 1
    assert points[0]["y"] == 100.0


def test_blue_alliance_wins_when_higher(ndb_stub) -> None:
    _put_event("2022casj", 2022)
    _put_match("2022casj", 2022, 1, 80, 100, datetime.datetime(2022, 3, 5))

    insights = compute_insights_for_year(2022, [HighScoreOverTimeV2Calculator()])

    assert len(insights) == 1
    pt = insights[0].data["series"][0]["points"][0]
    assert pt["y"] == 100.0
    assert pt["context"]["alliance"] == ["frc4", "frc5", "frc6"]


def test_matches_ordered_by_post_result_time_within_event(ndb_stub) -> None:
    # Match 2 was posted earlier than match 1 within the same event
    _put_event("2022casj", 2022)
    _put_match("2022casj", 2022, 1, 120, 90, datetime.datetime(2022, 3, 10))
    _put_match("2022casj", 2022, 2, 100, 80, datetime.datetime(2022, 3, 5))

    insights = compute_insights_for_year(2022, [HighScoreOverTimeV2Calculator()])

    assert len(insights) == 1
    points = insights[0].data["series"][0]["points"]
    # match 2 posted first (record=100), then match 1 breaks it (record=120)
    assert len(points) == 2
    assert points[0]["context"]["match_key"] == "2022casj_qm2"
    assert points[0]["y"] == 100.0
    assert points[1]["context"]["match_key"] == "2022casj_qm1"
    assert points[1]["y"] == 120.0


def test_post_result_time_stored_as_unix_timestamp(ndb_stub) -> None:
    t1 = datetime.datetime(2022, 3, 5, 12, 0, 0)
    t2 = datetime.datetime(2022, 3, 5, 14, 30, 0)
    _put_event("2022casj", 2022)
    _put_match("2022casj", 2022, 1, 100, 80, t1)
    _put_match("2022casj", 2022, 2, 120, 90, t2)

    insights = compute_insights_for_year(2022, [HighScoreOverTimeV2Calculator()])

    assert len(insights) == 1
    points = insights[0].data["series"][0]["points"]
    assert len(points) == 2
    assert points[0]["context"]["post_result_time"] == int(t1.timestamp())
    assert points[0]["context"]["is_current"] is False
    assert points[1]["context"]["post_result_time"] == int(t2.timestamp())


def test_unplayed_matches_skipped(ndb_stub) -> None:
    _put_event("2022casj", 2022)
    _put_match("2022casj", 2022, 1, -1, -1, datetime.datetime(2022, 3, 5))

    insights = compute_insights_for_year(2022, [HighScoreOverTimeV2Calculator()])

    assert insights == []


def test_no_matches_produces_no_insight(ndb_stub) -> None:
    _put_event("2022casj", 2022)

    insights = compute_insights_for_year(2022, [HighScoreOverTimeV2Calculator()])

    assert insights == []


def test_records_across_multiple_events_same_year(ndb_stub) -> None:
    _put_event("2022casj", 2022)
    _put_match("2022casj", 2022, 1, 80, 60, datetime.datetime(2022, 3, 5))

    _put_event("2022mnmi", 2022)
    _put_match("2022mnmi", 2022, 1, 100, 80, datetime.datetime(2022, 3, 12))

    _put_event("2022new", 2022)
    _put_match("2022new", 2022, 1, 95, 70, datetime.datetime(2022, 3, 19))

    insights = compute_insights_for_year(2022, [HighScoreOverTimeV2Calculator()])

    assert len(insights) == 1
    points = insights[0].data["series"][0]["points"]
    # Only casj and mnmi set records; new is lower than mnmi
    assert len(points) == 2
    assert points[0]["y"] == 80.0
    assert points[1]["y"] == 100.0
    assert points[1]["context"]["is_current"] is True


def test_concurrent_events_sorted_globally_by_time(ndb_stub) -> None:
    # Two events running the same week (alphabetically alhu < caclv).
    # caclv_qm2 was played BEFORE alhu_qm62, so alhu_qm62 (630) should not
    # appear in the record list because caclv_qm2 (748) already beat it.
    _put_event("2022alhu", 2022)
    _put_match("2022alhu", 2022, 1, 349, 200, datetime.datetime(2022, 3, 5, 10, 0, 0))
    _put_match("2022alhu", 2022, 62, 630, 400, datetime.datetime(2022, 3, 6, 16, 0, 0))

    _put_event("2022caclv", 2022)
    # caclv_qm2 played before alhu_qm62 but after alhu_qm1
    _put_match("2022caclv", 2022, 2, 748, 500, datetime.datetime(2022, 3, 6, 10, 0, 0))

    insights = compute_insights_for_year(2022, [HighScoreOverTimeV2Calculator()])

    assert len(insights) == 1
    points = insights[0].data["series"][0]["points"]
    # alhu_qm1 sets 349, caclv_qm2 sets 748 (before alhu_qm62), alhu_qm62 does not set a record
    assert len(points) == 2
    assert points[0]["context"]["match_key"] == "2022alhu_qm1"
    assert points[0]["y"] == 349.0
    assert points[1]["context"]["match_key"] == "2022caclv_qm2"
    assert points[1]["y"] == 748.0
    assert points[1]["context"]["is_current"] is True
    assert points[0]["context"]["post_result_time"] == int(
        datetime.datetime(2022, 3, 5, 10, 0, 0).timestamp()
    )
    assert points[1]["context"]["post_result_time"] == int(
        datetime.datetime(2022, 3, 6, 10, 0, 0).timestamp()
    )


def test_insight_stored_with_timeseries_category(ndb_stub) -> None:
    from backend.common.models.insight_v2 import InsightCategory

    _put_event("2022casj", 2022)
    _put_match("2022casj", 2022, 1, 100, 80, datetime.datetime(2022, 3, 5))

    insights = compute_insights_for_year(2022, [HighScoreOverTimeV2Calculator()])

    assert len(insights) == 1
    assert insights[0].category == InsightCategory.TIMESERIES
    assert insights[0].name == "high_score_over_time"
    assert insights[0].year == 2022


def test_foul_dominated_match_does_not_set_record(ndb_stub) -> None:
    # Match 1: 100 clean. Match 2: 374 total but 278 fouls -> 96 clean, not a record.
    _put_event("2022casj", 2022)
    _put_match("2022casj", 2022, 1, 100, 80, datetime.datetime(2022, 3, 5))
    _put_match(
        "2022casj",
        2022,
        2,
        374,
        4,
        datetime.datetime(2022, 3, 6),
        red_foul_points=278,
    )

    insights = compute_insights_for_year(2022, [HighScoreOverTimeV2Calculator()])

    assert len(insights) == 1
    points = insights[0].data["series"][0]["points"]
    assert len(points) == 1
    assert points[0]["y"] == 100.0
    assert points[0]["context"]["match_key"] == "2022casj_qm1"


def test_clean_score_is_used_for_record(ndb_stub) -> None:
    # Match 1: 100 clean. Match 2: 150 total but 60 fouls -> 90 clean, not a record.
    # Match 3: 110 total, 0 fouls -> 110 clean, breaks the record.
    _put_event("2022casj", 2022)
    _put_match("2022casj", 2022, 1, 100, 80, datetime.datetime(2022, 3, 5))
    _put_match(
        "2022casj",
        2022,
        2,
        150,
        20,
        datetime.datetime(2022, 3, 6),
        red_foul_points=60,
    )
    _put_match("2022casj", 2022, 3, 110, 90, datetime.datetime(2022, 3, 7))

    insights = compute_insights_for_year(2022, [HighScoreOverTimeV2Calculator()])

    assert len(insights) == 1
    points = insights[0].data["series"][0]["points"]
    assert len(points) == 2
    assert points[0]["y"] == 100.0
    assert points[1]["y"] == 110.0
    assert points[1]["context"]["match_key"] == "2022casj_qm3"
    assert points[1]["context"]["is_current"] is True


def test_foul_points_on_losing_alliance_ignored(ndb_stub) -> None:
    # Fouls on the losing (blue) alliance don't affect red's clean score.
    _put_event("2022casj", 2022)
    _put_match(
        "2022casj",
        2022,
        1,
        120,
        80,
        datetime.datetime(2022, 3, 5),
        blue_foul_points=10,
    )

    insights = compute_insights_for_year(2022, [HighScoreOverTimeV2Calculator()])

    assert len(insights) == 1
    points = insights[0].data["series"][0]["points"]
    assert len(points) == 1
    assert points[0]["y"] == 120.0
