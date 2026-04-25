from unittest.mock import patch

from backend.common.helpers.insights_v2.registry import make_all_insights


@patch(
    "backend.common.helpers.insights_v2.registry.compute_insights_for_year",
    return_value=[],
)
@patch(
    "backend.common.helpers.insights_v2.registry.LongestQualifyingEventStreakV2Calculator"
)
def test_streak_calculator_not_instantiated_for_specific_year(
    mock_streak, mock_compute
) -> None:
    make_all_insights(2024)
    mock_streak.assert_not_called()


@patch(
    "backend.common.helpers.insights_v2.registry.compute_insights_for_year",
    return_value=[],
)
@patch(
    "backend.common.helpers.insights_v2.registry.LongestQualifyingEventStreakV2Calculator"
)
def test_streak_calculator_instantiated_for_all_time(mock_streak, mock_compute) -> None:
    make_all_insights(0)
    mock_streak.assert_called_once_with()
