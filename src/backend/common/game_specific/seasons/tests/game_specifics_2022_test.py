from __future__ import annotations

from typing import cast

import pytest
from google.appengine.ext import ndb
from pyre_extensions import none_throws

from backend.common.consts.alliance_color import AllianceColor
from backend.common.consts.ranking_sort_orders import SORT_ORDER_INFO
from backend.common.frc_api.types import ScoreDetailModelAlliance2022
from backend.common.game_specific.seasons.game_specifics_2022 import GameSpecifics2022
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
