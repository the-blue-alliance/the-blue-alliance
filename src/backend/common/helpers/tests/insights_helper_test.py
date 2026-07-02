from types import SimpleNamespace
from typing import cast, Dict, List
from unittest import mock

from backend.common.helpers.insights_helper import InsightsHelper
from backend.common.helpers.insights_helper_utils import create_insight
from backend.common.models.event import Event
from backend.common.models.insight import Insight


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


def test_do_prediction_insights_for_events_scopes_to_district() -> None:
    fake_event = SimpleNamespace(
        event_type_enum=1,
        prep_details=mock.Mock(),
        prep_matches=mock.Mock(),
        details=SimpleNamespace(
            predictions={
                "match_predictions": {
                    "qual": {
                        "2024fim_qm1": {"winning_alliance": "red"},
                    },
                    "playoff": {},
                },
                "match_prediction_stats": {
                    "qual": {"brier_scores": {"win_loss": 0.25}},
                    "playoff": {"brier_scores": {"win_loss": 0.5}},
                },
            }
        ),
        matches=[
            SimpleNamespace(
                has_been_played=True,
                comp_level="qm",
                key=SimpleNamespace(id=lambda: "2024fim_qm1"),
                winning_alliance="red",
            )
        ],
    )

    insights = InsightsHelper._doPredictionInsightsForEvents(
        year=2024,
        events=cast(List[Event], [fake_event]),
        district_abbreviation="fim",
    )

    assert len(insights) == 1
    assert insights[0].district_abbreviation == "fim"
    assert insights[0].name == Insight.INSIGHT_NAMES[Insight.MATCH_PREDICTIONS]
    assert insights[0].data == {
        "qual": {
            "mean_brier_score": 0.25,
            "correct_matches_count": 1,
            "total_matches_count": 1,
            "mean_brier_score_cmp": None,
            "correct_matches_count_cmp": 0,
            "total_matches_count_cmp": 0,
        },
        "playoff": {
            "mean_brier_score": 0.5,
            "correct_matches_count": 0,
            "total_matches_count": 0,
            "mean_brier_score_cmp": None,
            "correct_matches_count_cmp": 0,
            "total_matches_count_cmp": 0,
        },
    }


@mock.patch("backend.common.helpers.insights_helper.DistrictEventsQuery")
@mock.patch("backend.common.helpers.insights_helper.DistrictHistoryQuery")
@mock.patch("backend.common.helpers.insights_helper.InsightsDistrictsHelper")
@mock.patch("backend.common.helpers.insights_helper.RenamedDistricts.get_latest_codes")
@mock.patch.object(InsightsHelper, "_doPredictionInsightsForEvents")
@mock.patch.object(InsightsHelper, "_doAwardInsightsForEvents")
@mock.patch.object(InsightsHelper, "_doMatchInsightsForEvents")
def test_do_district_insights_includes_season_style_stats(
    match_helper: mock.Mock,
    award_helper: mock.Mock,
    prediction_helper: mock.Mock,
    latest_codes: mock.Mock,
    district_helpers: mock.Mock,
    district_history_query: mock.Mock,
    district_events_query: mock.Mock,
) -> None:
    latest_codes.return_value = ["fim"]
    district_helpers.make_insight_team_data.return_value = {"frc1": {}}
    district_helpers.make_insight_district_data.return_value = {"district": {}}

    district = SimpleNamespace(year=2024, key_name="2024fim")
    district_history_query.return_value.fetch.return_value = [district]
    district_events = [SimpleNamespace(key_name="2024miket")]
    district_events_query.return_value.fetch.return_value = district_events

    match_helper.return_value = [
        create_insight(
            data={"matches": 1},
            name=Insight.INSIGHT_NAMES[Insight.NUM_MATCHES],
            year=2024,
            district_abbreviation="fim",
        )
    ]
    award_helper.return_value = [
        create_insight(
            data=["frc1"],
            name=Insight.INSIGHT_NAMES[Insight.BLUE_BANNERS],
            year=2024,
            district_abbreviation="fim",
        )
    ]
    prediction_helper.return_value = [
        create_insight(
            data={"qual": {}},
            name=Insight.INSIGHT_NAMES[Insight.MATCH_PREDICTIONS],
            year=2024,
            district_abbreviation="fim",
        )
    ]

    insights = InsightsHelper.doDistrictInsights()

    assert {
        (insight.name, insight.year, insight.district_abbreviation)
        for insight in insights
    } >= {
        (
            Insight.INSIGHT_NAMES[Insight.DISTRICT_INSIGHTS_TEAM_DATA],
            0,
            "fim",
        ),
        (
            Insight.INSIGHT_NAMES[Insight.DISTRICT_INSIGHT_DISTRICT_DATA],
            0,
            "fim",
        ),
        (Insight.INSIGHT_NAMES[Insight.NUM_MATCHES], 2024, "fim"),
        (Insight.INSIGHT_NAMES[Insight.BLUE_BANNERS], 2024, "fim"),
        (Insight.INSIGHT_NAMES[Insight.MATCH_PREDICTIONS], 2024, "fim"),
    }

    match_helper.assert_called_once_with(
        year=2024,
        events=district_events,
        district_abbreviation="fim",
    )
    award_helper.assert_called_once_with(
        year=2024,
        events=district_events,
        district_abbreviation="fim",
    )
    prediction_helper.assert_called_once_with(
        year=2024,
        events=district_events,
        district_abbreviation="fim",
    )


@mock.patch("backend.common.helpers.insights_helper.DistrictHistoryQuery")
@mock.patch("backend.common.helpers.insights_helper.InsightsDistrictsHelper")
@mock.patch.object(InsightsHelper, "_doDistrictInsightsForDistrictSeason")
def test_do_district_insights_for_abbreviation_year_skips_overall_aggregates(
    season_helper: mock.Mock,
    district_helpers: mock.Mock,
    district_history_query: mock.Mock,
) -> None:
    district = SimpleNamespace(year=2026, key_name="2026fim")
    district_history_query.return_value.fetch.return_value = [district]

    season_insight = create_insight(
        data={"matches": 1},
        name=Insight.INSIGHT_NAMES[Insight.NUM_MATCHES],
        year=2026,
        district_abbreviation="fim",
    )
    season_helper.return_value = [season_insight]

    insights = InsightsHelper.doDistrictInsightsForAbbreviation("fim", year=2026)

    assert insights == [season_insight]
    district_helpers.make_insight_team_data.assert_not_called()
    district_helpers.make_insight_district_data.assert_not_called()
    season_helper.assert_called_once_with(
        district_abbreviation="fim",
        district=district,
    )


def test_do_overall_award_insights_does_not_double_count_district_blue_banners(
    ndb_stub,
) -> None:
    """
    doOverallAwardInsights aggregates BLUE_BANNERS from per-year insights.
    District-scoped insights (district_abbreviation set) must be excluded,
    otherwise banners from district events are double-counted: once in the
    global per-year insight and once in the district-scoped per-year insight.
    """
    # Global per-year insight: frc1 won 3 banners in 2024
    global_insight = create_insight(
        data=[(3, ["frc1"])],
        name=Insight.INSIGHT_NAMES[Insight.BLUE_BANNERS],
        year=2024,
    )
    global_insight.put()

    # District-scoped per-year insight: frc1 won 2 of those 3 banners at FIM events.
    # These are already included in the global insight above.
    district_insight = create_insight(
        data=[(2, ["frc1"])],
        name=Insight.INSIGHT_NAMES[Insight.BLUE_BANNERS],
        year=2024,
        district_abbreviation="fim",
    )
    district_insight.put()

    insights = InsightsHelper.doOverallAwardInsights()

    blue_banner_insight = next(
        (i for i in insights if i.name == Insight.INSIGHT_NAMES[Insight.BLUE_BANNERS]),
        None,
    )
    assert blue_banner_insight is not None
    frc1_count = next(
        (count for count, teams in blue_banner_insight.data if "frc1" in teams),
        None,
    )
    # Should be 3 (from global insight only), not 5 (3+2 double-count)
    assert frc1_count == 3


def test_do_overall_award_insights_does_not_double_count_district_regional_winners(
    ndb_stub,
) -> None:
    """
    REGIONAL_DISTRICT_WINNERS includes district event winners (not CMP).
    District-scoped insights must be excluded from the all-time aggregation.
    """
    create_insight(
        data=[(2, ["frc1"])],
        name=Insight.INSIGHT_NAMES[Insight.REGIONAL_DISTRICT_WINNERS],
        year=2024,
    ).put()

    create_insight(
        data=[(1, ["frc1"])],
        name=Insight.INSIGHT_NAMES[Insight.REGIONAL_DISTRICT_WINNERS],
        year=2024,
        district_abbreviation="fim",
    ).put()

    insights = InsightsHelper.doOverallAwardInsights()

    regional_insight = next(
        (
            i
            for i in insights
            if i.name == Insight.INSIGHT_NAMES[Insight.REGIONAL_DISTRICT_WINNERS]
        ),
        None,
    )
    assert regional_insight is not None
    frc1_count = next(
        (count for count, teams in regional_insight.data if "frc1" in teams),
        None,
    )
    # Should be 2 (from global insight only), not 3 (2+1 double-count)
    assert frc1_count == 2


def test_do_overall_award_insights_does_not_double_count_district_rca_winners(
    ndb_stub,
) -> None:
    """
    RCA_WINNERS includes Chairman's at district championships.
    District-scoped insights must be excluded from the all-time aggregation.
    """
    create_insight(
        data=["frc1"],
        name=Insight.INSIGHT_NAMES[Insight.RCA_WINNERS],
        year=2024,
    ).put()

    create_insight(
        data=["frc1"],
        name=Insight.INSIGHT_NAMES[Insight.RCA_WINNERS],
        year=2024,
        district_abbreviation="fim",
    ).put()

    insights = InsightsHelper.doOverallAwardInsights()

    rca_insight = next(
        (i for i in insights if i.name == Insight.INSIGHT_NAMES[Insight.RCA_WINNERS]),
        None,
    )
    assert rca_insight is not None
    frc1_count = next(
        (count for count, teams in rca_insight.data if "frc1" in teams),
        None,
    )
    # Should be 1 (from global insight only), not 2 (double-count)
    assert frc1_count == 1


def test_do_overall_award_insights_does_not_double_count_district_elim_teamups(
    ndb_stub,
) -> None:
    """
    SUCCESSFUL_ELIM_TEAMUPS includes winners from district events.
    District-scoped insights must be excluded from the all-time aggregation.
    """
    create_insight(
        data=[["frc1", "frc2", "frc3"]],
        name=Insight.INSIGHT_NAMES[Insight.SUCCESSFUL_ELIM_TEAMUPS],
        year=2024,
    ).put()

    create_insight(
        data=[["frc1", "frc2", "frc3"]],
        name=Insight.INSIGHT_NAMES[Insight.SUCCESSFUL_ELIM_TEAMUPS],
        year=2024,
        district_abbreviation="fim",
    ).put()

    insights = InsightsHelper.doOverallAwardInsights()

    teamup_insight = next(
        (
            i
            for i in insights
            if i.name == Insight.INSIGHT_NAMES[Insight.SUCCESSFUL_ELIM_TEAMUPS]
        ),
        None,
    )
    assert teamup_insight is not None
    # Find the count for the frc1+frc2 pair; should be 1 (global only), not 2 (double-count)
    frc1_frc2_count = next(
        (
            count
            for count, pairs in teamup_insight.data
            if ["frc1", "frc2"] in pairs
            or any("frc1" in p and "frc2" in p for p in pairs)
        ),
        None,
    )
    assert frc1_frc2_count == 1


def test_do_overall_match_insights_does_not_include_district_num_matches(
    ndb_stub,
) -> None:
    """
    NUM_MATCHES is produced for district events too.
    District-scoped insights must be excluded from the all-time aggregation,
    otherwise a year appears multiple times in the historical data.
    """
    create_insight(
        data=100,
        name=Insight.INSIGHT_NAMES[Insight.NUM_MATCHES],
        year=2024,
    ).put()

    create_insight(
        data=40,
        name=Insight.INSIGHT_NAMES[Insight.NUM_MATCHES],
        year=2024,
        district_abbreviation="fim",
    ).put()

    insights = InsightsHelper.doOverallMatchInsights()

    num_matches_insight = next(
        (i for i in insights if i.name == Insight.INSIGHT_NAMES[Insight.NUM_MATCHES]),
        None,
    )
    assert num_matches_insight is not None
    year_2024_entries = [
        (year, count) for year, count in num_matches_insight.data if year == 2024
    ]
    # Should be exactly one entry for 2024 (the global insight with count=100)
    assert year_2024_entries == [(2024, 100)]
