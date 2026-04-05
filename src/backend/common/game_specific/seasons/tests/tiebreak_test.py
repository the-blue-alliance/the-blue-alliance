import os

import pytest
from pyre_extensions import none_throws

from backend.common.consts.alliance_color import AllianceColor
from backend.common.game_specific.registry import _REGISTRY
from backend.common.game_specific.seasons.game_specifics_2016 import GameSpecifics2016
from backend.common.game_specific.seasons.game_specifics_2017 import GameSpecifics2017
from backend.common.game_specific.seasons.game_specifics_2019 import GameSpecifics2019
from backend.common.game_specific.seasons.game_specifics_2020 import GameSpecifics2020
from backend.common.game_specific.seasons.game_specifics_2022 import GameSpecifics2022
from backend.common.game_specific.seasons.game_specifics_2023 import GameSpecifics2023
from backend.common.game_specific.seasons.game_specifics_2024 import GameSpecifics2024
from backend.common.game_specific.seasons.game_specifics_2025 import GameSpecifics2025
from backend.common.game_specific.seasons.game_specifics_2026 import GameSpecifics2026
from backend.common.models.match import Match

# Sentinel path: dirname(_HELPERS_TESTS) == .../helpers/tests/
_HELPERS_TESTS = os.path.join(os.path.dirname(__file__), "../../../helpers/tests/x")


@pytest.fixture(autouse=True)
def auto_add_ndb_context(ndb_context) -> None:
    pass


def _tiebreak_winner(criteria):
    """Walk criteria list and return winning alliance color or empty string."""
    for c in criteria:
        if c is None:
            break
        if c[0] > c[1]:
            return AllianceColor.RED
        elif c[1] > c[0]:
            return AllianceColor.BLUE
    return ""


# ── No-tiebreaker seasons ─────────────────────────────────────────────────────


@pytest.mark.parametrize("year", [2006, 2007, 2008, 2009, 2011, 2012, 2013, 2014])
def test_no_tiebreakers_early_seasons(year: int) -> None:
    game = _REGISTRY[year]
    assert game.tiebreak_criteria({}, {}) == []


# ── finals_can_be_tiebroken ───────────────────────────────────────────────────


def test_finals_can_be_tiebroken_2016() -> None:
    assert GameSpecifics2016().finals_can_be_tiebroken() is True


@pytest.mark.parametrize("year", [2017, 2023, 2026])
def test_finals_cannot_be_tiebroken(year: int) -> None:
    assert _REGISTRY[year].finals_can_be_tiebroken() is False


# ── Per-season tiebreaker tests ───────────────────────────────────────────────


def test_2016_tiebreakers(test_data_importer) -> None:
    test_data_importer.import_match(_HELPERS_TESTS, "data/2016cmp_f1m3.json")
    match: Match = none_throws(Match.get_by_id("2016cmp_f1m3"))
    red = none_throws(match.score_breakdown)[AllianceColor.RED]
    blue = none_throws(match.score_breakdown)[AllianceColor.BLUE]
    criteria = GameSpecifics2016().tiebreak_criteria(red, blue)
    assert _tiebreak_winner(criteria) == AllianceColor.RED


def test_2017_tiebreakers(test_data_importer) -> None:
    test_data_importer.import_match(_HELPERS_TESTS, "data/2017dal_qf3m2.json")
    match: Match = none_throws(Match.get_by_id("2017dal_qf3m2"))
    red = none_throws(match.score_breakdown)[AllianceColor.RED]
    blue = none_throws(match.score_breakdown)[AllianceColor.BLUE]
    criteria = GameSpecifics2017().tiebreak_criteria(red, blue)
    assert _tiebreak_winner(criteria) == AllianceColor.RED


def test_2019_tiebreakers(test_data_importer) -> None:
    test_data_importer.import_match(_HELPERS_TESTS, "data/2019hiho_qf4m1.json")
    match: Match = none_throws(Match.get_by_id("2019hiho_qf4m1"))
    red = none_throws(match.score_breakdown)[AllianceColor.RED]
    blue = none_throws(match.score_breakdown)[AllianceColor.BLUE]
    criteria = GameSpecifics2019().tiebreak_criteria(red, blue)
    assert _tiebreak_winner(criteria) == AllianceColor.RED


def test_2020_tiebreakers(test_data_importer) -> None:
    test_data_importer.import_match(_HELPERS_TESTS, "data/2020mndu2_sf2m2.json")
    match: Match = none_throws(Match.get_by_id("2020mndu2_sf2m2"))
    red = none_throws(match.score_breakdown)[AllianceColor.RED]
    blue = none_throws(match.score_breakdown)[AllianceColor.BLUE]
    criteria = GameSpecifics2020().tiebreak_criteria(red, blue)
    assert _tiebreak_winner(criteria) == AllianceColor.BLUE


def test_2022_tiebreakers(test_data_importer) -> None:
    test_data_importer.import_match(_HELPERS_TESTS, "data/2022wasam_qf2m2.json")
    match: Match = none_throws(Match.get_by_id("2022wasam_qf2m2"))
    red = none_throws(match.score_breakdown)[AllianceColor.RED]
    blue = none_throws(match.score_breakdown)[AllianceColor.BLUE]
    criteria = GameSpecifics2022().tiebreak_criteria(red, blue)
    assert _tiebreak_winner(criteria) == AllianceColor.BLUE


def test_2023_tiebreakers(test_data_importer) -> None:
    test_data_importer.import_match(_HELPERS_TESTS, "data/2023cmptx_sf12m1.json")
    match: Match = none_throws(Match.get_by_id("2023cmptx_sf12m1"))
    red = none_throws(match.score_breakdown)[AllianceColor.RED]
    blue = none_throws(match.score_breakdown)[AllianceColor.BLUE]
    criteria = GameSpecifics2023().tiebreak_criteria(red, blue)
    assert _tiebreak_winner(criteria) == AllianceColor.RED


def test_2024_tiebreakers_fouls(test_data_importer) -> None:
    test_data_importer.import_match(_HELPERS_TESTS, "data/2024miket_sf13m1.json")
    match: Match = none_throws(Match.get_by_id("2024miket_sf13m1"))
    red = none_throws(match.score_breakdown)[AllianceColor.RED]
    blue = none_throws(match.score_breakdown)[AllianceColor.BLUE]
    criteria = GameSpecifics2024().tiebreak_criteria(red, blue)
    assert _tiebreak_winner(criteria) == AllianceColor.RED


def test_2024_tiebreakers_auto(test_data_importer) -> None:
    test_data_importer.import_match(_HELPERS_TESTS, "data/2024isde1_sf12m1.json")
    match: Match = none_throws(Match.get_by_id("2024isde1_sf12m1"))
    red = none_throws(match.score_breakdown)[AllianceColor.RED]
    blue = none_throws(match.score_breakdown)[AllianceColor.BLUE]
    criteria = GameSpecifics2024().tiebreak_criteria(red, blue)
    assert _tiebreak_winner(criteria) == AllianceColor.RED


def test_2025_tiebreakers_fouls(test_data_importer) -> None:
    test_data_importer.import_match(_HELPERS_TESTS, "data/2025nhsal_sf7m1.json")
    match: Match = none_throws(Match.get_by_id("2025nhsal_sf7m1"))
    red = none_throws(match.score_breakdown)[AllianceColor.RED]
    blue = none_throws(match.score_breakdown)[AllianceColor.BLUE]
    criteria = GameSpecifics2025().tiebreak_criteria(red, blue)
    assert _tiebreak_winner(criteria) == AllianceColor.BLUE


def test_2025_tiebreakers_auto(test_data_importer) -> None:
    test_data_importer.import_match(_HELPERS_TESTS, "data/2025vagle_sf8m1.json")
    match: Match = none_throws(Match.get_by_id("2025vagle_sf8m1"))
    red = none_throws(match.score_breakdown)[AllianceColor.RED]
    blue = none_throws(match.score_breakdown)[AllianceColor.BLUE]
    criteria = GameSpecifics2025().tiebreak_criteria(red, blue)
    assert _tiebreak_winner(criteria) == AllianceColor.BLUE


def test_2026_tiebreakers_auto_fuel(test_data_importer) -> None:
    # 2026 FMA District Philadelphia SF10-1: tied 108–108;
    # 2nd criterion (ALLIANCE AUTO FUEL points) awards the win to blue (35 vs 21).
    test_data_importer.import_match(_HELPERS_TESTS, "data/2026paphi_sf10m1.json")
    match: Match = none_throws(Match.get_by_id("2026paphi_sf10m1"))
    red = none_throws(match.score_breakdown)[AllianceColor.RED]
    blue = none_throws(match.score_breakdown)[AllianceColor.BLUE]
    criteria = GameSpecifics2026().tiebreak_criteria(red, blue)
    assert _tiebreak_winner(criteria) == AllianceColor.BLUE


def test_2026_tiebreakers_major_foul(test_data_importer) -> None:
    # 2026 FSC District Richland SF5-1: tied 66–66;
    # 1st criterion (opponent major fouls) awards the win to red (blue committed 1 major).
    test_data_importer.import_match(_HELPERS_TESTS, "data/2026schop_sf5m1.json")
    match: Match = none_throws(Match.get_by_id("2026schop_sf5m1"))
    red = none_throws(match.score_breakdown)[AllianceColor.RED]
    blue = none_throws(match.score_breakdown)[AllianceColor.BLUE]
    criteria = GameSpecifics2026().tiebreak_criteria(red, blue)
    assert _tiebreak_winner(criteria) == AllianceColor.RED
