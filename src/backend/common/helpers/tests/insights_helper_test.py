from typing import Dict, List

from backend.common.helpers.insights_helper import InsightsHelper


def call_calc_streaks(division_winners_map: Dict[str, List[int]]) -> Dict[str, int]:
    # Helper to call the static method.
    # The _calculate_einstein_streaks method returns a dict.
    return InsightsHelper._calculate_einstein_streaks(division_winners_map)


def test_frc254_einstein_streak():
    data = {"frc254": [2017, 2018, 2019, 2022]}
    expected = {"frc254": 4}
    assert call_calc_streaks(data) == expected


def test_unsorted_input_years():
    data = {"frc123": [2022, 2017, 2019, 2018]}
    expected = {"frc123": 4}
    assert call_calc_streaks(data) == expected


def test_streak_broken_by_normal_gap():
    data = {"frc456": [2015, 2016, 2018]}
    # Streak from 2015-2016 (length 2). 2018 is a new streak of 1. The longest streak is 2.
    expected = {"frc456": 2}
    assert call_calc_streaks(data) == expected


def test_streak_of_one_single_year_win():
    data = {"frc789": [2018]}
    expected = {"frc789": 1}
    assert call_calc_streaks(data) == expected


def test_no_wins_empty_list():
    data = {"frc000": []}
    expected = {"frc000": 0}
    assert call_calc_streaks(data) == expected


def test_no_wins_team_not_present():
    data = {}
    expected = {}
    assert call_calc_streaks(data) == expected


def test_multiple_teams():
    data = {"frc254": [2017, 2018, 2019, 2022], "frc789": [2018], "frc000": []}
    expected = {"frc254": 4, "frc789": 1, "frc000": 0}
    assert call_calc_streaks(data) == expected


def test_streak_ending_before_covid_gap():
    data = {"frc111": [2016, 2017, 2018]}
    expected = {"frc111": 3}
    assert call_calc_streaks(data) == expected


def test_streak_starting_after_2022():
    # Assuming 2023, 2024 are valid years post-COVID special logic
    data = {"frc222": [2023, 2024]}
    expected = {"frc222": 2}
    assert call_calc_streaks(data) == expected

    data_single = {"frc223": [2023]}
    expected_single = {"frc223": 1}
    assert call_calc_streaks(data_single) == expected_single


def test_win_in_2019_only_edge_of_covid_gap():
    data = {"frc333": [2019]}
    expected = {"frc333": 1}
    assert call_calc_streaks(data) == expected


def test_win_in_2022_only_edge_of_covid_gap():
    data = {"frc444": [2022]}
    expected = {"frc444": 1}
    assert call_calc_streaks(data) == expected


def test_longer_streak_bridging_covid_gap():
    data = {"frc555": [2015, 2016, 2017, 2018, 2019, 2022, 2023, 2024]}
    expected = {"frc555": 8}
    assert call_calc_streaks(data) == expected


def test_streak_broken_before_covid_gap_then_win_in_2022():
    data = {"frc666": [2016, 2017, 2022]}
    # Streak from 2016-2017 (length 2). 2022 is a new streak of 1. The longest streak is 2.
    expected = {"frc666": 2}
    assert call_calc_streaks(data) == expected


def test_empty_overall_input_map():
    data = {}
    expected = {}
    assert call_calc_streaks(data) == expected
