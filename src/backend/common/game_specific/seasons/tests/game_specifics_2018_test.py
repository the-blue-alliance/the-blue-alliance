from __future__ import annotations

import json
import logging

from typing import cast

import pytest
from google.appengine.ext import ndb
from pyre_extensions import none_throws

from backend.common.consts.event_type import EventType
from backend.common.consts.ranking_sort_orders import SORT_ORDER_INFO
from backend.common.frc_api.types import ScoreDetailModelAlliance2018
from backend.common.game_specific.seasons.game_specifics_2018 import GameSpecifics2018
from backend.common.game_specific.seasons.tests.conftest import (
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
    assert GameSpecifics2018().ranking_sort_order_info() == SORT_ORDER_INFO[2018]


def test_valid_score_breakdown_keys() -> None:
    keys = GameSpecifics2018().valid_score_breakdown_keys()
    assert "totalPoints" in keys
    assert "autoPoints" in keys
    assert len(keys) > 5


def test_finals_can_be_tiebroken() -> None:
    assert GameSpecifics2018().finals_can_be_tiebroken() is False


def test_calculate_event_insights(test_data_importer) -> None:
    test_data_importer.import_match_list(HELPERS_TESTS, "data/2018nyny_matches.json")
    matches = Match.query(Match.event == ndb.Key(Event, "2018nyny")).fetch()
    insights = GameSpecifics2018().calculate_event_insights(matches)
    with open(
        test_data_importer._get_path(HELPERS_TESTS, "data/2018nyny_insights.json"), "r"
    ) as f:
        expected = json.load(f)
    # Strip key excluded from comparison for known data reason
    assert insights is not None
    del none_throws(insights["qual"])["winning_opp_switch_denial_percentage_teleop"]
    del none_throws(insights["playoff"])["winning_opp_switch_denial_percentage_teleop"]
    del none_throws(expected["qual"])["winning_opp_switch_denial_percentage_teleop"]
    del none_throws(expected["playoff"])["winning_opp_switch_denial_percentage_teleop"]
    assert insights == expected


def test_get_prediction_relevant_stats() -> None:
    stats = GameSpecifics2018().get_prediction_relevant_stats()
    assert len(stats) > 0
    assert stats[0][0] == "score"


def test_round_robin_tiebreak_keys() -> None:
    assert GameSpecifics2018().round_robin_tiebreak_keys() == [
        "endgamePoints",
        "autoPoints",
    ]


def test_round_robin_tiebreaker_names() -> None:
    assert GameSpecifics2018().round_robin_tiebreaker_names() == [
        "Park/Climb Points",
        "Auto Points",
    ]


def test_tiebreak_criteria_has_no_criteria() -> None:
    # 2018 playoff ties were not broken by score breakdown fields.
    empty = cast(ScoreDetailModelAlliance2018, {})
    assert GameSpecifics2018().tiebreak_criteria(empty, empty) == []
    assert tiebreak_winner([]) == ""


# A played match whose breakdown lacks every scoring field FIRST publishes.
_BROKEN_BREAKDOWN = {"red": {}, "blue": {}}


def test_calculate_event_insights_ignores_unplayed_and_breakdownless_matches() -> None:
    matches = [
        build_match("2018test", "qm", 1, -1, -1, None),
        build_match("2018test", "qm", 2, 30, 10, None),
    ]
    assert GameSpecifics2018().calculate_event_insights(matches) == {
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
    put_event("2018test", event_type)
    broken = build_match("2018test", "qm", 1, 30, 10, _BROKEN_BREAKDOWN)
    with caplog.at_level(logging.INFO):
        insights = GameSpecifics2018().calculate_event_insights([broken])
    assert insights == {"qual": None, "playoff": None}
    failures = [
        record
        for record in caplog.records
        if record.getMessage().startswith("Event insights failed for 2018test_qm1")
    ]
    assert failures
    assert all(record.levelno == level for record in failures)
