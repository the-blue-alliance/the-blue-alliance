from __future__ import annotations

import json

import pytest
from google.appengine.ext import ndb
from pyre_extensions import none_throws

from backend.common.consts.ranking_sort_orders import SORT_ORDER_INFO
from backend.common.game_specific.seasons.game_specifics_2018 import GameSpecifics2018
from backend.common.game_specific.seasons.tests.conftest import HELPERS_TESTS
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
