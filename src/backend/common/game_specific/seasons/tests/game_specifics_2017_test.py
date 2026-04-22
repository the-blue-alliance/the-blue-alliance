from __future__ import annotations

import json

from typing import cast

import pytest
from google.appengine.ext import ndb
from pyre_extensions import none_throws

from backend.common.consts.alliance_color import AllianceColor
from backend.common.consts.ranking_sort_orders import SORT_ORDER_INFO
from backend.common.frc_api.types import ScoreDetailModelAlliance2017
from backend.common.game_specific.seasons.game_specifics_2017 import GameSpecifics2017
from backend.common.game_specific.seasons.tests.conftest import (
    HELPERS_TESTS,
    tiebreak_winner,
)
from backend.common.models.event import Event
from backend.common.models.match import Match


@pytest.fixture(autouse=True)
def auto_add_ndb_context(ndb_context) -> None:
    pass


def test_ranking_sort_order_info() -> None:
    assert GameSpecifics2017().ranking_sort_order_info() == SORT_ORDER_INFO[2017]


def test_valid_score_breakdown_keys() -> None:
    keys = GameSpecifics2017().valid_score_breakdown_keys()
    assert "totalPoints" in keys
    assert "autoPoints" in keys
    assert len(keys) > 5


def test_finals_can_be_tiebroken() -> None:
    assert GameSpecifics2017().finals_can_be_tiebroken() is False


def test_tiebreak_criteria(test_data_importer) -> None:
    test_data_importer.import_match(HELPERS_TESTS, "data/2017dal_qf3m2.json")
    match: Match = none_throws(Match.get_by_id("2017dal_qf3m2"))
    red = cast(
        ScoreDetailModelAlliance2017,
        none_throws(match.score_breakdown)[AllianceColor.RED],
    )
    blue = cast(
        ScoreDetailModelAlliance2017,
        none_throws(match.score_breakdown)[AllianceColor.BLUE],
    )
    assert (
        tiebreak_winner(GameSpecifics2017().tiebreak_criteria(red, blue))
        == AllianceColor.RED
    )


def test_calculate_event_insights(test_data_importer) -> None:
    test_data_importer.import_match_list(HELPERS_TESTS, "data/2017nyny_matches.json")
    matches = Match.query(Match.event == ndb.Key(Event, "2017nyny")).fetch()
    insights = GameSpecifics2017().calculate_event_insights(matches)
    with open(
        test_data_importer._get_path(HELPERS_TESTS, "data/2017nyny_insights.json"), "r"
    ) as f:
        expected = json.load(f)
    assert insights == expected


def test_get_prediction_relevant_stats() -> None:
    stats = GameSpecifics2017().get_prediction_relevant_stats()
    assert len(stats) > 0
    assert stats[0][0] == "score"


def test_prediction_ranking_fields() -> None:
    game = GameSpecifics2017()
    assert game.prediction_brier_fields() == [
        ("kPaRankingPointAchieved", "prob_pressure", "pressure"),
        ("rotorRankingPointAchieved", "prob_gears", "gears"),
    ]
    assert game.ranking_bonus_rp_breakdown_fields() == [
        "kPaRankingPointAchieved",
        "rotorRankingPointAchieved",
    ]
    assert game.ranking_bonus_rp_prediction_fields() == [
        "prob_pressure",
        "prob_gears",
    ]
    assert game.ranking_tiebreaker_breakdown_field() == "totalPoints"
    assert game.ranking_tiebreaker_prediction_field() == "score"
    assert game.ranking_win_points() == 2


def test_round_robin_tiebreak_keys() -> None:
    assert GameSpecifics2017().round_robin_tiebreak_keys() == ["totalPoints"]


def test_round_robin_tiebreaker_names() -> None:
    assert GameSpecifics2017().round_robin_tiebreaker_names() == ["Match Points"]
