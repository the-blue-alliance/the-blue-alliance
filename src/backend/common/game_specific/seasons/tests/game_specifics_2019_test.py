from __future__ import annotations

import json

from typing import cast

import pytest
from google.appengine.ext import ndb
from pyre_extensions import none_throws

from backend.common.consts.alliance_color import AllianceColor
from backend.common.consts.ranking_sort_orders import SORT_ORDER_INFO
from backend.common.frc_api.types import ScoreDetailModelAlliance2019
from backend.common.game_specific.seasons.game_specifics_2019 import GameSpecifics2019
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
    assert GameSpecifics2019().ranking_sort_order_info() == SORT_ORDER_INFO[2019]


def test_valid_score_breakdown_keys() -> None:
    keys = GameSpecifics2019().valid_score_breakdown_keys()
    assert "totalPoints" in keys
    assert "autoPoints" in keys
    assert len(keys) > 5


def test_finals_can_be_tiebroken() -> None:
    assert GameSpecifics2019().finals_can_be_tiebroken() is False


def test_tiebreak_criteria(test_data_importer) -> None:
    test_data_importer.import_match(HELPERS_TESTS, "data/2019hiho_qf4m1.json")
    match: Match = none_throws(Match.get_by_id("2019hiho_qf4m1"))
    red = cast(
        ScoreDetailModelAlliance2019,
        none_throws(match.score_breakdown)[AllianceColor.RED],
    )
    blue = cast(
        ScoreDetailModelAlliance2019,
        none_throws(match.score_breakdown)[AllianceColor.BLUE],
    )
    assert (
        tiebreak_winner(GameSpecifics2019().tiebreak_criteria(red, blue))
        == AllianceColor.RED
    )


def test_calculate_event_insights(test_data_importer) -> None:
    test_data_importer.import_match_list(HELPERS_TESTS, "data/2019nyny_matches.json")
    matches = Match.query(Match.event == ndb.Key(Event, "2019nyny")).fetch()
    insights = GameSpecifics2019().calculate_event_insights(matches)
    with open(
        test_data_importer._get_path(HELPERS_TESTS, "data/2019nyny_insights.json"), "r"
    ) as f:
        expected = json.load(f)
    assert insights == expected


def test_get_manual_coprs() -> None:
    coprs = GameSpecifics2019().get_manual_coprs()
    assert "Cargo + Panel Points" in coprs


def test_get_prediction_relevant_stats() -> None:
    stats = GameSpecifics2019().get_prediction_relevant_stats()
    assert len(stats) > 0
    assert stats[0][0] == "score"


def test_round_robin_tiebreak_keys() -> None:
    assert GameSpecifics2019().round_robin_tiebreak_keys() == [
        "cargoPoints",
        "hatchPanelPoints",
    ]


def test_round_robin_tiebreaker_names() -> None:
    assert GameSpecifics2019().round_robin_tiebreaker_names() == [
        "Cargo Points",
        "Hatch Panel Points",
    ]
