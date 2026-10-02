from __future__ import annotations

import json
import logging

from typing import cast

import pytest
from google.appengine.ext import ndb
from pyre_extensions import none_throws

from backend.common.consts.alliance_color import AllianceColor
from backend.common.consts.event_type import EventType
from backend.common.consts.ranking_sort_orders import SORT_ORDER_INFO
from backend.common.frc_api.types import ScoreDetailModelAlliance2016
from backend.common.game_specific.seasons.game_specifics_2016 import GameSpecifics2016
from backend.common.game_specific.seasons.tests.conftest import (
    assert_partial_breakdowns_split_counters,
    assert_score_stats_without_breakdowns,
    build_match,
    HELPERS_TESTS,
    put_event,
    tiebreak_winner,
)
from backend.common.models.event import Event
from backend.common.models.match import Match


@pytest.fixture(autouse=True)
def auto_add_ndb_context(ndb_context) -> None:
    pass


def test_ranking_sort_order_info() -> None:
    assert GameSpecifics2016().ranking_sort_order_info() == SORT_ORDER_INFO[2016]


def test_valid_score_breakdown_keys() -> None:
    keys = GameSpecifics2016().valid_score_breakdown_keys()
    assert "totalPoints" in keys
    assert "autoPoints" in keys
    assert len(keys) > 5


def test_finals_can_be_tiebroken() -> None:
    assert GameSpecifics2016().finals_can_be_tiebroken() is True


def test_tiebreak_criteria(test_data_importer) -> None:
    test_data_importer.import_match(HELPERS_TESTS, "data/2016cmp_f1m3.json")
    match: Match = none_throws(Match.get_by_id("2016cmp_f1m3"))
    red = cast(
        ScoreDetailModelAlliance2016,
        none_throws(match.score_breakdown)[AllianceColor.RED],
    )
    blue = cast(
        ScoreDetailModelAlliance2016,
        none_throws(match.score_breakdown)[AllianceColor.BLUE],
    )
    assert (
        tiebreak_winner(GameSpecifics2016().tiebreak_criteria(red, blue))
        == AllianceColor.RED
    )


def test_calculate_event_insights(test_data_importer) -> None:
    test_data_importer.import_match_list(HELPERS_TESTS, "data/2016nyny_matches.json")
    matches = Match.query(Match.event == ndb.Key(Event, "2016nyny")).fetch()
    insights = GameSpecifics2016().calculate_event_insights(matches)
    with open(
        test_data_importer._get_path(HELPERS_TESTS, "data/2016nyny_insights.json"), "r"
    ) as f:
        expected = json.load(f)
    assert insights == expected


def test_get_prediction_relevant_stats() -> None:
    stats = GameSpecifics2016().get_prediction_relevant_stats()
    assert len(stats) > 0
    assert stats[0][0] == "score"


def test_prediction_ranking_fields() -> None:
    game = GameSpecifics2016()
    assert game.prediction_brier_fields() == [
        ("teleopDefensesBreached", "prob_breach", "breach"),
        ("teleopTowerCaptured", "prob_capture", "capture"),
    ]
    assert game.ranking_bonus_rp_breakdown_fields() == [
        "teleopDefensesBreached",
        "teleopTowerCaptured",
    ]
    assert game.ranking_bonus_rp_prediction_fields() == [
        "prob_breach",
        "prob_capture",
    ]
    assert game.ranking_tiebreaker_breakdown_field() == "autoPoints"
    assert game.ranking_tiebreaker_prediction_field() == "auto_points"
    assert game.ranking_win_points() == 2


def test_tiebreak_criteria_without_breakdown_data() -> None:
    empty = cast(ScoreDetailModelAlliance2016, {})
    criteria = GameSpecifics2016().tiebreak_criteria(empty, empty)
    assert criteria == [None] * 6
    assert tiebreak_winner(criteria) == ""


# A played match whose breakdown lacks every scoring field FIRST publishes.
_BROKEN_BREAKDOWN = {"red": {}, "blue": {}}


def test_calculate_event_insights_ignores_unplayed_matches() -> None:
    matches = [build_match("2016test", "qm", 1, -1, -1, None)]
    assert GameSpecifics2016().calculate_event_insights(matches) == {
        "qual": None,
        "playoff": None,
    }


@pytest.mark.parametrize(
    "event_type, level",
    [(EventType.REGIONAL, logging.WARNING), (EventType.OFFSEASON, logging.INFO)],
)
def test_calculate_event_insights_logs_failed_matches(
    event_type: EventType, level: int, caplog: pytest.LogCaptureFixture
) -> None:
    put_event("2016test", event_type)
    broken = build_match("2016test", "qm", 1, 30, 10, _BROKEN_BREAKDOWN)
    with caplog.at_level(logging.INFO):
        insights = GameSpecifics2016().calculate_event_insights([broken])
    assert insights is not None and insights["qual"] is not None
    failures = [
        record
        for record in caplog.records
        if record.getMessage().startswith("Event insights failed for 2016test_qm1")
    ]
    assert failures
    assert all(record.levelno == level for record in failures)


def test_insights_without_any_breakdowns() -> None:
    assert_score_stats_without_breakdowns(GameSpecifics2016(), "2016test")


def test_insights_with_some_breakdowns(test_data_importer) -> None:
    test_data_importer.import_match_list(HELPERS_TESTS, "data/2016nyny_matches.json")
    matches = Match.query(Match.event == ndb.Key(Event, "2016nyny")).fetch()
    assert_partial_breakdowns_split_counters(GameSpecifics2016(), matches)
