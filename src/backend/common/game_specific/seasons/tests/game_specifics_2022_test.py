from __future__ import annotations

import json
import logging

from typing import cast

import pytest
from google.appengine.ext import ndb
from pyre_extensions import none_throws

from backend.common.consts.alliance_color import ALLIANCE_COLORS, AllianceColor
from backend.common.consts.event_type import EventType
from backend.common.consts.ranking_sort_orders import SORT_ORDER_INFO
from backend.common.frc_api.types import ScoreDetailModelAlliance2022
from backend.common.game_specific.seasons.game_specifics_2022 import GameSpecifics2022
from backend.common.game_specific.seasons.tests.conftest import (
    assert_breakdownless_match_excluded,
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
    assert GameSpecifics2022().ranking_sort_order_info() == SORT_ORDER_INFO[2022]


def test_valid_score_breakdown_keys() -> None:
    keys = GameSpecifics2022().valid_score_breakdown_keys()
    assert "totalPoints" in keys
    assert "autoPoints" in keys
    assert len(keys) > 5


def test_finals_can_be_tiebroken() -> None:
    assert GameSpecifics2022().finals_can_be_tiebroken() is False


def test_tiebreak_criteria(test_data_importer) -> None:
    test_data_importer.import_match(HELPERS_TESTS, "data/2022wasam_qf2m2.json")
    match: Match = none_throws(Match.get_by_id("2022wasam_qf2m2"))
    red = cast(
        ScoreDetailModelAlliance2022,
        none_throws(match.score_breakdown)[AllianceColor.RED],
    )
    blue = cast(
        ScoreDetailModelAlliance2022,
        none_throws(match.score_breakdown)[AllianceColor.BLUE],
    )
    assert (
        tiebreak_winner(GameSpecifics2022().tiebreak_criteria(red, blue))
        == AllianceColor.BLUE
    )


def test_calculate_event_insights(test_data_importer) -> None:
    test_data_importer.import_match_list(HELPERS_TESTS, "data/2022cmptx_matches.json")
    matches = Match.query(Match.event == ndb.Key(Event, "2022cmptx")).fetch()
    insights = GameSpecifics2022().calculate_event_insights(matches)
    assert insights is not None


def test_get_prediction_relevant_stats() -> None:
    stats = GameSpecifics2022().get_prediction_relevant_stats()
    assert len(stats) > 0
    assert stats[0][0] == "score"


def test_round_robin_tiebreak_keys() -> None:
    assert GameSpecifics2022().round_robin_tiebreak_keys() == [
        "endgamePoints",
        "autoPoints",
    ]


def test_round_robin_tiebreaker_names() -> None:
    assert GameSpecifics2022().round_robin_tiebreaker_names() == [
        "Hangar Points",
        "Auto Taxi/Cargo Points",
    ]


def test_tiebreak_criteria_without_breakdown_data() -> None:
    empty = cast(ScoreDetailModelAlliance2022, {})
    criteria = GameSpecifics2022().tiebreak_criteria(empty, empty)
    assert criteria == [None] * 3
    assert tiebreak_winner(criteria) == ""


# A played match whose breakdown lacks every scoring field FIRST publishes.
_BROKEN_BREAKDOWN = {"red": {}, "blue": {}}


def test_calculate_event_insights_ignores_unplayed_and_breakdownless_matches() -> None:
    matches = [
        build_match("2022test", "qm", 1, -1, -1, None),
        build_match("2022test", "qm", 2, 30, 10, None),
    ]
    assert GameSpecifics2022().calculate_event_insights(matches) == {
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
    put_event("2022test", event_type)
    broken = build_match("2022test", "qm", 1, 30, 10, _BROKEN_BREAKDOWN)
    with caplog.at_level(logging.INFO):
        insights = GameSpecifics2022().calculate_event_insights([broken])
    assert insights == {"qual": None, "playoff": None}
    failures = [
        record
        for record in caplog.records
        if record.getMessage().startswith("Event insights failed for 2022test_qm1")
    ]
    assert failures
    assert all(record.levelno == level for record in failures)


def test_calculate_event_insights_counts_low_climbs_in_quals(
    test_data_importer,
) -> None:
    source = test_data_importer.parse_match_list(
        HELPERS_TESTS, "data/2022cmptx_matches.json"
    )[0]
    red_score = source.alliances[AllianceColor.RED]["score"]
    blue_score = source.alliances[AllianceColor.BLUE]["score"]
    breakdown = json.loads(none_throws(source.score_breakdown_json))
    for color in ALLIANCE_COLORS:
        for i in range(1, 4):
            breakdown[color][f"endgameRobot{i}"] = "None"

    no_climbs = build_match("2022cmptx", "qm", 1, red_score, blue_score, breakdown)
    insights = none_throws(GameSpecifics2022().calculate_event_insights([no_climbs]))
    assert insights["playoff"] is None
    assert none_throws(insights["qual"])["low_climb_count"] == [0, 6, 0.0]

    breakdown["red"]["endgameRobot1"] = "Low"
    one_low = build_match("2022cmptx", "qm", 1, red_score, blue_score, breakdown)
    insights = none_throws(GameSpecifics2022().calculate_event_insights([one_low]))
    assert none_throws(insights["qual"])["low_climb_count"] == [1, 6, 100.0 / 6]


def test_bug_20_breakdownless_match_excluded_from_insights(
    test_data_importer,
) -> None:
    """
    Bug #20: a played match without a score breakdown skews the insights.
    Its scores are added to the totals before the breakdown check, but
    it is never counted in finished_matches, so it skews the averages.
    Correct: exclude it from both numerator and denominator, so the insights
    are identical to the event's insights without it.
    """
    test_data_importer.import_match_list(HELPERS_TESTS, "data/2022cmptx_matches.json")
    matches = Match.query(Match.event == ndb.Key(Event, "2022cmptx")).fetch()
    assert_breakdownless_match_excluded(GameSpecifics2022(), matches)
