from __future__ import annotations

import logging

from typing import cast

import pytest
from google.appengine.ext import ndb
from pyre_extensions import none_throws

from backend.common.consts.alliance_color import AllianceColor
from backend.common.consts.event_type import EventType
from backend.common.consts.ranking_sort_orders import SORT_ORDER_INFO
from backend.common.frc_api.types import ScoreDetailModelAlliance2023
from backend.common.game_specific.seasons.game_specifics_2023 import GameSpecifics2023
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
    assert GameSpecifics2023().ranking_sort_order_info() == SORT_ORDER_INFO[2023]


def test_valid_score_breakdown_keys() -> None:
    keys = GameSpecifics2023().valid_score_breakdown_keys()
    assert "totalPoints" in keys
    assert "autoPoints" in keys
    assert len(keys) > 5


def test_finals_can_be_tiebroken() -> None:
    assert GameSpecifics2023().finals_can_be_tiebroken() is False


def test_tiebreak_criteria(test_data_importer) -> None:
    test_data_importer.import_match(HELPERS_TESTS, "data/2023cmptx_sf12m1.json")
    match: Match = none_throws(Match.get_by_id("2023cmptx_sf12m1"))
    red = cast(
        ScoreDetailModelAlliance2023,
        none_throws(match.score_breakdown)[AllianceColor.RED],
    )
    blue = cast(
        ScoreDetailModelAlliance2023,
        none_throws(match.score_breakdown)[AllianceColor.BLUE],
    )
    assert (
        tiebreak_winner(GameSpecifics2023().tiebreak_criteria(red, blue))
        == AllianceColor.RED
    )


def test_calculate_event_insights(test_data_importer) -> None:
    test_data_importer.import_match_list(HELPERS_TESTS, "data/2023njfla_matches.json")
    matches = Match.query(Match.event == ndb.Key(Event, "2023njfla")).fetch()
    insights = GameSpecifics2023().calculate_event_insights(matches)
    assert insights is not None


def test_get_manual_coprs() -> None:
    coprs = GameSpecifics2023().get_manual_coprs()
    assert len(coprs) > 0


def test_get_prediction_relevant_stats() -> None:
    stats = GameSpecifics2023().get_prediction_relevant_stats()
    assert len(stats) > 0
    assert stats[0][0] == "score"


def test_tiebreak_criteria_without_breakdown_data() -> None:
    empty = cast(ScoreDetailModelAlliance2023, {})
    criteria = GameSpecifics2023().tiebreak_criteria(empty, empty)
    assert criteria == [None] * 3
    assert tiebreak_winner(criteria) == ""


# A played match whose breakdown lacks every scoring field FIRST publishes.
_BROKEN_BREAKDOWN = {"red": {}, "blue": {}}


def test_calculate_event_insights_ignores_unplayed_matches() -> None:
    matches = [build_match("2023test", "qm", 1, -1, -1, None)]
    assert GameSpecifics2023().calculate_event_insights(matches) == {
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
    put_event("2023test", event_type)
    broken = build_match("2023test", "qm", 1, 30, 10, _BROKEN_BREAKDOWN)
    with caplog.at_level(logging.INFO):
        insights = GameSpecifics2023().calculate_event_insights([broken])
    assert insights is not None and insights["qual"] is not None
    failures = [
        record
        for record in caplog.records
        if record.getMessage().startswith("Event insights failed for 2023test_qm1")
    ]
    assert failures
    assert all(record.levelno == level for record in failures)


def test_insights_without_any_breakdowns() -> None:
    assert_score_stats_without_breakdowns(GameSpecifics2023(), "2023test")


def test_insights_with_some_breakdowns(test_data_importer) -> None:
    test_data_importer.import_match_list(HELPERS_TESTS, "data/2023njfla_matches.json")
    matches = Match.query(Match.event == ndb.Key(Event, "2023njfla")).fetch()
    assert_partial_breakdowns_split_counters(GameSpecifics2023(), matches)
