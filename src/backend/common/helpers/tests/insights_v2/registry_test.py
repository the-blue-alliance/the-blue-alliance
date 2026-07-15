from unittest.mock import patch

import pytest

from backend.common.helpers.insights_v2.registry import make_all_insights


@patch(
    "backend.common.helpers.insights_v2.registry.compute_insights_for_year",
    return_value=[],
)
@patch("backend.common.helpers.insights_v2.registry.LongestEinsteinStreakV2Calculator")
@patch(
    "backend.common.helpers.insights_v2.registry.LongestQualifyingEventStreakV2Calculator"
)
def test_streak_calculators_not_instantiated_for_specific_year(
    mock_qualifying, mock_einstein, mock_compute
) -> None:
    make_all_insights(2024)
    mock_qualifying.assert_not_called()
    mock_einstein.assert_not_called()


@patch(
    "backend.common.helpers.insights_v2.registry.compute_insights_for_year",
    return_value=[],
)
@patch("backend.common.helpers.insights_v2.registry.LongestEinsteinStreakV2Calculator")
@patch(
    "backend.common.helpers.insights_v2.registry.LongestQualifyingEventStreakV2Calculator"
)
def test_streak_calculators_instantiated_for_all_time(
    mock_qualifying, mock_einstein, mock_compute
) -> None:
    make_all_insights(0)
    mock_qualifying.assert_called_once_with()
    mock_einstein.assert_called_once_with()


@patch(
    "backend.common.helpers.insights_v2.registry.compute_insights_for_year",
    return_value=[],
)
@patch("backend.common.helpers.insights_v2.registry.MostDivisionWinsV2Calculator")
def test_most_division_wins_only_for_all_time(mock_calc, mock_compute) -> None:
    make_all_insights(0)
    mock_calc.assert_called_once_with()


@patch(
    "backend.common.helpers.insights_v2.registry.compute_insights_for_year",
    return_value=[],
)
@patch("backend.common.helpers.insights_v2.registry.MostDivisionWinsV2Calculator")
def test_most_division_wins_not_for_specific_year(mock_calc, mock_compute) -> None:
    make_all_insights(2024)
    mock_calc.assert_not_called()


@pytest.mark.parametrize("year", [2024, 2026])
@patch(
    "backend.common.helpers.insights_v2.registry.compute_insights_for_year",
    return_value=[],
)
@patch("backend.common.helpers.insights_v2.registry.HighestEndgameScoreV2Calculator")
def test_highest_endgame_score_included_for_supported_years(
    mock_calc, mock_compute, year: int
) -> None:
    make_all_insights(year)
    mock_calc.assert_called_once_with()


@pytest.mark.parametrize("year", [2017, 2018, 2023, 2025])
@patch(
    "backend.common.helpers.insights_v2.registry.compute_insights_for_year",
    return_value=[],
)
@patch("backend.common.helpers.insights_v2.registry.HighestEndgameScoreV2Calculator")
def test_highest_endgame_score_excluded_for_unsupported_years(
    mock_calc, mock_compute, year: int
) -> None:
    make_all_insights(year)
    mock_calc.assert_not_called()


@patch(
    "backend.common.helpers.insights_v2.registry.compute_insights_for_year",
    return_value=[],
)
@patch(
    "backend.common.helpers.insights_v2.registry.MostDivisionFinalsAppearancesV2Calculator"
)
def test_most_division_finals_appearances_only_for_all_time(
    mock_calc, mock_compute
) -> None:
    make_all_insights(0)
    mock_calc.assert_called_once_with()


@patch(
    "backend.common.helpers.insights_v2.registry.compute_insights_for_year",
    return_value=[],
)
@patch(
    "backend.common.helpers.insights_v2.registry.MostDivisionFinalsAppearancesV2Calculator"
)
def test_most_division_finals_appearances_not_for_specific_year(
    mock_calc, mock_compute
) -> None:
    make_all_insights(2024)
    mock_calc.assert_not_called()


@patch(
    "backend.common.helpers.insights_v2.registry.compute_insights_for_year",
    return_value=[],
)
@patch("backend.common.helpers.insights_v2.registry.MostDistrictCmpWinsV2Calculator")
def test_most_district_cmp_wins_only_for_all_time(mock_calc, mock_compute) -> None:
    make_all_insights(0)
    mock_calc.assert_called_once_with()


@patch(
    "backend.common.helpers.insights_v2.registry.compute_insights_for_year",
    return_value=[],
)
@patch("backend.common.helpers.insights_v2.registry.MostDistrictCmpWinsV2Calculator")
def test_most_district_cmp_wins_not_for_specific_year(mock_calc, mock_compute) -> None:
    make_all_insights(2024)
    mock_calc.assert_not_called()


@pytest.mark.parametrize("year", [2016, 2017, 2019, 2020, 2022, 2023, 2024, 2025, 2026])
@patch(
    "backend.common.helpers.insights_v2.registry.compute_insights_for_year",
    return_value=[],
)
@patch("backend.common.helpers.insights_v2.registry.MostGamePiecesScoredV2Calculator")
def test_most_game_pieces_scored_included_for_supported_years(
    mock_calc, mock_compute, year: int
) -> None:
    make_all_insights(year)
    mock_calc.assert_called_once_with()


@pytest.mark.parametrize("year", [0, 2018, 2021])
@patch(
    "backend.common.helpers.insights_v2.registry.compute_insights_for_year",
    return_value=[],
)
@patch("backend.common.helpers.insights_v2.registry.MostGamePiecesScoredV2Calculator")
def test_most_game_pieces_scored_excluded_for_unsupported_years(
    mock_calc, mock_compute, year: int
) -> None:
    make_all_insights(year)
    mock_calc.assert_not_called()
