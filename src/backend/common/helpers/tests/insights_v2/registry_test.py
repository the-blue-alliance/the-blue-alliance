from unittest.mock import patch

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
