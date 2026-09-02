from __future__ import annotations

import json
from typing import cast

import pytest
from google.appengine.ext import ndb
from pyre_extensions import none_throws

from backend.common.consts.alliance_color import AllianceColor
from backend.common.consts.ranking_sort_orders import SORT_ORDER_INFO
from backend.common.frc_api.types import ScoreDetailModelAlliance2024
from backend.common.game_specific.seasons.game_specifics_2024 import GameSpecifics2024
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
    assert GameSpecifics2024().ranking_sort_order_info() == SORT_ORDER_INFO[2024]


def test_valid_score_breakdown_keys() -> None:
    keys = GameSpecifics2024().valid_score_breakdown_keys()
    assert "totalPoints" in keys
    assert "autoPoints" in keys
    assert len(keys) > 5


def test_finals_can_be_tiebroken() -> None:
    assert GameSpecifics2024().finals_can_be_tiebroken() is False


def test_tiebreak_criteria_fouls(test_data_importer) -> None:
    test_data_importer.import_match(HELPERS_TESTS, "data/2024miket_sf13m1.json")
    match: Match = none_throws(Match.get_by_id("2024miket_sf13m1"))
    red = cast(
        ScoreDetailModelAlliance2024,
        none_throws(match.score_breakdown)[AllianceColor.RED],
    )
    blue = cast(
        ScoreDetailModelAlliance2024,
        none_throws(match.score_breakdown)[AllianceColor.BLUE],
    )
    assert (
        tiebreak_winner(GameSpecifics2024().tiebreak_criteria(red, blue))
        == AllianceColor.RED
    )


def test_tiebreak_criteria_auto(test_data_importer) -> None:
    test_data_importer.import_match(HELPERS_TESTS, "data/2024isde1_sf12m1.json")
    match: Match = none_throws(Match.get_by_id("2024isde1_sf12m1"))
    red = cast(
        ScoreDetailModelAlliance2024,
        none_throws(match.score_breakdown)[AllianceColor.RED],
    )
    blue = cast(
        ScoreDetailModelAlliance2024,
        none_throws(match.score_breakdown)[AllianceColor.BLUE],
    )
    assert (
        tiebreak_winner(GameSpecifics2024().tiebreak_criteria(red, blue))
        == AllianceColor.RED
    )


def test_calculate_event_insights(test_data_importer) -> None:
    test_data_importer.import_match_list(HELPERS_TESTS, "data/2024nytr_matches.json")
    matches = Match.query(Match.event == ndb.Key(Event, "2024nytr")).fetch()
    insights = GameSpecifics2024().calculate_event_insights(matches)
    assert insights is not None


def test_get_manual_coprs() -> None:
    coprs = GameSpecifics2024().get_manual_coprs()
    assert len(coprs) > 0


def test_get_prediction_relevant_stats() -> None:
    stats = GameSpecifics2024().get_prediction_relevant_stats()
    assert len(stats) > 0
    assert stats[0][0] == "score"


def _success_rate_match(
    red_score: int,
    blue_score: int,
    red: dict | None = None,
    blue: dict | None = None,
    with_breakdown: bool = True,
) -> Match:
    def alliance(overrides: dict | None) -> dict:
        breakdown = {
            "melodyBonusAchieved": False,
            "ensembleBonusAchieved": False,
            "autoPoints": 0,
        }
        breakdown.update(overrides or {})
        return breakdown

    return Match(
        id="2024casj_qm1",
        comp_level="qm",
        event=ndb.Key(Event, "2024casj"),
        year=2024,
        match_number=1,
        set_number=1,
        team_key_names=["frc1", "frc2", "frc3", "frc4", "frc5", "frc6"],
        alliances_json=json.dumps(
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
        ),
        score_breakdown_json=(
            json.dumps({"red": alliance(red), "blue": alliance(blue)})
            if with_breakdown
            else None
        ),
    )


def _measure(match: Match) -> dict:
    return {
        counter.name: counter.measure(match)
        for counter in GameSpecifics2024().success_rate_counters()
    }


def test_success_rate_counter_names_and_labels() -> None:
    counters = GameSpecifics2024().success_rate_counters()
    assert [(c.name, c.label) for c in counters] == [
        ("rp_1", "Melody RP"),
        ("rp_2", "Ensemble RP"),
        ("max_alliance_rp", "4 RP"),
        ("max_match_rp", "6 RP"),
        ("auto_win_conversion", "Auto Win Conversion"),
    ]


def test_success_rate_auto_win_conversion() -> None:
    match = _success_rate_match(100, 80, red={"autoPoints": 10})
    assert _measure(match)["auto_win_conversion"] == (1, 1)

    match = _success_rate_match(80, 100, red={"autoPoints": 10})
    assert _measure(match)["auto_win_conversion"] == (0, 1)


def test_success_rate_auto_win_conversion_needs_both_winners() -> None:
    match = _success_rate_match(
        100, 80, red={"autoPoints": 10}, blue={"autoPoints": 10}
    )
    assert _measure(match)["auto_win_conversion"] == (0, 0)

    match = _success_rate_match(80, 80, red={"autoPoints": 10})
    assert _measure(match)["auto_win_conversion"] == (0, 0)


def test_success_rate_auto_win_conversion_needs_auto_points() -> None:
    match = _success_rate_match(
        100, 80, red={"autoPoints": None}, blue={"autoPoints": None}
    )
    assert _measure(match)["auto_win_conversion"] == (0, 0)

    match = _success_rate_match(100, 80, with_breakdown=False)
    assert _measure(match)["auto_win_conversion"] == (0, 0)
