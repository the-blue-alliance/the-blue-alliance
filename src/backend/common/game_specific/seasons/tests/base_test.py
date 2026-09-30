from __future__ import annotations

import pytest

from backend.common.game_specific.base import (
    DefaultSeasonGameConfig,
    NoBonusRankingPointsMixin,
    NoQualAverageInRankingsMixin,
    RecordInRankingsMixin,
    SeasonGameConfig,
)
from backend.common.game_specific.seasons.default import DefaultGame
from backend.common.game_specific.seasons.game_specifics_2010 import GameSpecifics2010
from backend.common.game_specific.seasons.game_specifics_2021 import GameSpecifics2021
from backend.common.game_specific.seasons.game_specifics_2026 import GameSpecifics2026


def test_cannot_instantiate_abstract_root() -> None:
    with pytest.raises(TypeError):
        SeasonGameConfig()  # pyre-ignore[45]


@pytest.mark.parametrize(
    "method_name, args",
    [
        ("tiebreak_criteria", ({}, {})),
        ("finals_can_be_tiebroken", ()),
        ("calculate_event_insights", ([],)),
        ("get_manual_coprs", ()),
        ("get_prediction_relevant_stats", ()),
        ("prediction_brier_fields", ()),
        ("ranking_bonus_rp_breakdown_fields", ()),
        ("ranking_bonus_rp_prediction_fields", ()),
        ("ranking_tiebreaker_breakdown_field", ()),
        ("ranking_tiebreaker_prediction_field", ()),
        ("ranking_win_points", ()),
        ("valid_score_breakdown_keys", ()),
        ("ranking_sort_order_info", ()),
        ("record_in_rankings", ()),
        ("qual_average_in_rankings", ()),
        ("round_robin_tiebreak_keys", ()),
        ("round_robin_tiebreaker_names", ()),
    ],
)
def test_abstract_hooks_raise_when_not_overridden(
    method_name: str, args: tuple
) -> None:
    # Call the abstract root's implementation directly on a concrete instance
    # so a season that forgets to override a hook fails loudly instead of
    # silently inheriting a default.
    hook = getattr(SeasonGameConfig, method_name)
    with pytest.raises(NotImplementedError):
        hook(DefaultGame(), *args)


def test_root_defaults_track_nothing() -> None:
    game = DefaultGame()
    assert game.ranking_bonus_rp_labels() == []
    assert game.success_rate_counters() == []


def test_default_season_game_config_is_a_no_op() -> None:
    game = DefaultGame()
    assert isinstance(game, DefaultSeasonGameConfig)
    assert game.tiebreak_criteria({}, {}) == []
    assert game.finals_can_be_tiebroken() is False
    assert game.calculate_event_insights([]) is None
    assert game.get_manual_coprs() == {}
    assert game.get_prediction_relevant_stats() == []
    assert game.prediction_brier_fields() == []
    assert game.ranking_bonus_rp_breakdown_fields() == []
    assert game.ranking_bonus_rp_prediction_fields() == []
    assert game.ranking_tiebreaker_breakdown_field() is None
    assert game.ranking_tiebreaker_prediction_field() is None
    assert game.ranking_win_points() == 2
    assert game.valid_score_breakdown_keys() == set()
    assert game.ranking_sort_order_info() is None
    assert game.record_in_rankings() is True
    assert game.qual_average_in_rankings() is False
    assert game.round_robin_tiebreak_keys() == []
    assert game.round_robin_tiebreaker_names() == []


def test_ranking_mixins() -> None:
    assert RecordInRankingsMixin().record_in_rankings() is True
    assert NoQualAverageInRankingsMixin().qual_average_in_rankings() is False


def test_no_bonus_ranking_points_mixin() -> None:
    mixin = NoBonusRankingPointsMixin()
    assert mixin.ranking_bonus_rp_breakdown_fields() == []
    assert mixin.ranking_bonus_rp_prediction_fields() == []

    # Historical seasons inherit the mixin and therefore declare no bonus RPs.
    historical = GameSpecifics2010()
    assert historical.ranking_bonus_rp_breakdown_fields() == []
    assert historical.ranking_bonus_rp_prediction_fields() == []


def test_modern_game_config_defaults() -> None:
    # 2021 overrides the fewest hooks of any modern season, so it exposes the
    # AbstractModernGameConfig defaults for everything it does not define.
    remote_season = GameSpecifics2021()
    assert remote_season.finals_can_be_tiebroken() is False
    assert remote_season.get_manual_coprs() == {}
    assert remote_season.prediction_brier_fields() == []
    assert remote_season.qual_average_in_rankings() is False
    assert remote_season.ranking_win_points() == 2

    # Seasons that do not opt out of W/L/T keep the modern default.
    assert GameSpecifics2026().record_in_rankings() is True
    assert GameSpecifics2026().round_robin_tiebreak_keys() == []
    assert GameSpecifics2026().round_robin_tiebreaker_names() == []
