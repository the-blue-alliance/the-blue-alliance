import datetime
import json
import re
from types import SimpleNamespace
from typing import Any, cast, Dict, List, Optional, Set
from unittest import mock

from google.appengine.ext import ndb
from pyre_extensions import none_throws

from backend.common.consts.award_type import AwardType
from backend.common.consts.comp_level import CompLevel
from backend.common.consts.event_type import EventType, SEASON_EVENT_TYPES
from backend.common.helpers.event_helper import FOC_LABEL
from backend.common.helpers.insights_helper import InsightsHelper
from backend.common.helpers.insights_helper_utils import create_insight
from backend.common.models.award import Award
from backend.common.models.event import Event
from backend.common.models.insight import Insight
from backend.common.models.match import Match
from backend.common.models.team import Team


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


def _put_event(
    event_key: str,
    event_type: EventType,
    start_date: Optional[datetime.datetime] = None,
    official: Optional[bool] = None,
    name: Optional[str] = None,
) -> Event:
    year = int(event_key[:4])
    event = Event(
        id=event_key,
        year=year,
        event_short=event_key[4:],
        event_type_enum=event_type,
        name=name or event_key,
        official=(event_type in SEASON_EVENT_TYPES) if official is None else official,
        start_date=start_date,
        end_date=(start_date + datetime.timedelta(days=2)) if start_date else None,
    )
    event.put()
    return event


def _put_match(
    event_key: str,
    short_key: str,
    red_score: int,
    blue_score: int,
    red_teams: Optional[List[str]] = None,
    blue_teams: Optional[List[str]] = None,
    youtube_videos: Optional[List[str]] = None,
) -> Match:
    red_teams = red_teams or ["frc1", "frc2", "frc3"]
    blue_teams = blue_teams or ["frc4", "frc5", "frc6"]
    key_match = none_throws(re.match(r"^([a-z]+)(\d+)(?:m(\d+))?$", short_key))
    comp_level = CompLevel(key_match.group(1))
    if key_match.group(3) is None:  # qual matches are "qm<match>"
        set_number, match_number = 1, int(key_match.group(2))
    else:
        set_number, match_number = int(key_match.group(2)), int(key_match.group(3))
    match = Match(
        id=f"{event_key}_{short_key}",
        event=ndb.Key(Event, event_key),
        year=int(event_key[:4]),
        comp_level=comp_level,
        set_number=set_number,
        match_number=match_number,
        team_key_names=red_teams + blue_teams,
        alliances_json=json.dumps(
            {
                "red": {"teams": red_teams, "score": red_score},
                "blue": {"teams": blue_teams, "score": blue_score},
            }
        ),
        youtube_videos=youtube_videos or [],
    )
    match.put()
    return match


def _put_award(
    event_key: str,
    award_type: AwardType,
    team_keys: List[str],
    event_type: EventType,
) -> None:
    Award(
        id=f"{event_key}_{award_type}",
        year=int(event_key[:4]),
        award_type_enum=award_type,
        event_type_enum=event_type,
        event=ndb.Key(Event, event_key),
        name_str=str(award_type),
        team_list=[ndb.Key(Team, team_key) for team_key in team_keys],
    ).put()


def _insights_by_name(insights: List[Insight]) -> Dict[str, Insight]:
    by_name = {insight.name: insight for insight in insights}
    assert len(by_name) == len(insights), "duplicate insight names"
    return by_name


def _match_keys(match_data: List[Dict[str, Any]]) -> Set[str]:
    return {data["key_name"] for data in match_data}


def test_do_match_insights_computes_all_match_stats(ndb_stub) -> None:
    """
    Two official regionals a week apart, an offseason event (never counted)
    and an unofficial Festival of Champions (grouped into its own week but its
    matches are skipped). 2014 has no year-specific game insights, so every
    other match insight is exercised with hand-computable numbers.
    """
    _put_event(
        "2014wk1",
        EventType.REGIONAL,
        start_date=datetime.datetime(2014, 3, 6),
        name="Week One Regional",
    )
    _put_event(
        "2014wk2",
        EventType.REGIONAL,
        start_date=datetime.datetime(2014, 3, 13),
        name="Week Two Regional",
    )
    _put_event("2014off", EventType.OFFSEASON, start_date=datetime.datetime(2014, 7, 1))
    _put_event("2014foc", EventType.FOC, official=False)

    # Week 1: red wins, blue wins, unplayed, and a tied final
    _put_match("2014wk1", "qm1", 50, 30)
    _put_match("2014wk1", "qm2", 20, 60, youtube_videos=["abc123"])
    _put_match("2014wk1", "qm3", -1, -1, red_teams=["frc7", "frc8", "frc9"])
    _put_match("2014wk1", "f1m1", 70, 70)
    # Week 2: a qual and a quarterfinal that tie for the week's high score
    _put_match("2014wk2", "qm1", 80, 10)
    _put_match("2014wk2", "qf1m1", 40, 80)
    # Offseason and unofficial FOC matches must never count
    _put_match("2014off", "qm1", 500, 500)
    _put_match("2014foc", "f1m1", 900, 900)

    insights = InsightsHelper.doMatchInsights(2014)
    by_name = _insights_by_name(insights)

    assert set(by_name.keys()) == {
        Insight.INSIGHT_NAMES[Insight.MATCH_HIGHSCORE_BY_WEEK],
        Insight.INSIGHT_NAMES[Insight.MATCH_HIGHSCORE],
        Insight.INSIGHT_NAMES[Insight.MATCH_AVERAGES_BY_WEEK],
        Insight.INSIGHT_NAMES[Insight.ELIM_MATCH_AVERAGES_BY_WEEK],
        Insight.INSIGHT_NAMES[Insight.MATCH_AVERAGE_MARGINS_BY_WEEK],
        Insight.INSIGHT_NAMES[Insight.ELIM_MATCH_AVERAGE_MARGINS_BY_WEEK],
        Insight.INSIGHT_NAMES[Insight.SCORE_DISTRIBUTION],
        Insight.INSIGHT_NAMES[Insight.ELIM_SCORE_DISTRIBUTION],
        Insight.INSIGHT_NAMES[Insight.WINNING_MARGIN_DISTRIBUTION],
        Insight.INSIGHT_NAMES[Insight.ELIM_WINNING_MARGIN_DISTRIBUTION],
        Insight.INSIGHT_NAMES[Insight.NUM_MATCHES],
        Insight.INSIGHT_NAMES[Insight.MATCHES_PLAYED],
    }
    for insight in insights:
        assert insight.year == 2014
        assert insight.district_abbreviation is None

    # Unplayed matches still count towards the total
    assert by_name[Insight.INSIGHT_NAMES[Insight.NUM_MATCHES]].data == 6

    highscore_by_week = by_name[
        Insight.INSIGHT_NAMES[Insight.MATCH_HIGHSCORE_BY_WEEK]
    ].data
    assert [week for week, _ in highscore_by_week] == [
        "Week 1",
        "Week 2",
        FOC_LABEL,
    ]
    assert _match_keys(highscore_by_week[0][1]) == {"2014wk1_f1m1"}
    assert _match_keys(highscore_by_week[1][1]) == {"2014wk2_qm1", "2014wk2_qf1m1"}
    assert highscore_by_week[2][1] == []

    highscore = by_name[Insight.INSIGHT_NAMES[Insight.MATCH_HIGHSCORE]].data
    assert _match_keys(highscore["overall"]) == {"2014wk2_qm1", "2014wk2_qf1m1"}
    assert _match_keys(highscore["qual"]) == {"2014wk2_qm1"}
    assert _match_keys(highscore["playoff"]) == {"2014wk2_qf1m1"}

    # _generateMatchData carries the front-end rendering fields
    qm1_data = next(m for m in highscore["qual"] if m["key_name"] == "2014wk2_qm1")
    assert qm1_data == {
        "key_name": "2014wk2_qm1",
        "verbose_name": "Quals 1",
        "event_name": "Week Two Regional",
        "alliances": {
            "red": {
                "teams": ["frc1", "frc2", "frc3"],
                "score": 80,
                "surrogates": [],
                "dqs": [],
            },
            "blue": {
                "teams": ["frc4", "frc5", "frc6"],
                "score": 10,
                "surrogates": [],
                "dqs": [],
            },
        },
        "score_breakdown": None,
        "winning_alliance": "red",
        "tba_video": None,
        "youtube_videos_formatted": [],
    }

    assert by_name[Insight.INSIGHT_NAMES[Insight.MATCH_AVERAGES_BY_WEEK]].data == [
        ["Week 1", 50.0],
        ["Week 2", 52.5],
    ]
    assert by_name[Insight.INSIGHT_NAMES[Insight.ELIM_MATCH_AVERAGES_BY_WEEK]].data == [
        ["Week 1", 70.0],
        ["Week 2", 60.0],
    ]
    assert by_name[
        Insight.INSIGHT_NAMES[Insight.MATCH_AVERAGE_MARGINS_BY_WEEK]
    ].data == [["Week 1", 20.0], ["Week 2", 55.0]]
    assert by_name[
        Insight.INSIGHT_NAMES[Insight.ELIM_MATCH_AVERAGE_MARGINS_BY_WEEK]
    ].data == [["Week 1", 0.0], ["Week 2", 40.0]]

    # High score 80 -> bin width 4, centred at +2. JSON round trip stringifies keys.
    assert by_name[Insight.INSIGHT_NAMES[Insight.SCORE_DISTRIBUTION]].data == {
        "10.0": 10.0,
        "22.0": 10.0,
        "30.0": 10.0,
        "42.0": 10.0,
        "50.0": 10.0,
        "62.0": 10.0,
        "70.0": 20.0,
        "82.0": 20.0,
    }
    assert by_name[Insight.INSIGHT_NAMES[Insight.ELIM_SCORE_DISTRIBUTION]].data == {
        "42.0": 25.0,
        "70.0": 50.0,
        "82.0": 25.0,
    }
    # Margins 20, 40, 0, 70, 40 -> high margin 70, bin width 4
    assert by_name[Insight.INSIGHT_NAMES[Insight.WINNING_MARGIN_DISTRIBUTION]].data == {
        "2.0": 20.0,
        "22.0": 20.0,
        "42.0": 40.0,
        "70.0": 20.0,
    }
    assert by_name[
        Insight.INSIGHT_NAMES[Insight.ELIM_WINNING_MARGIN_DISTRIBUTION]
    ].data == {"2.0": 50.0, "42.0": 50.0}

    # Teams in the unplayed match are not counted
    assert by_name[Insight.INSIGHT_NAMES[Insight.MATCHES_PLAYED]].data == [
        [5, ["frc1", "frc2", "frc3", "frc4", "frc5", "frc6"]]
    ]


def test_do_match_insights_with_no_events_has_empty_counts(ndb_stub) -> None:
    insights = InsightsHelper.doMatchInsights(2014)
    by_name = _insights_by_name(insights)

    assert by_name[Insight.INSIGHT_NAMES[Insight.NUM_MATCHES]].data == 0
    assert by_name[Insight.INSIGHT_NAMES[Insight.MATCHES_PLAYED]].data == []


def test_do_match_insights_penalty_free_highscores_and_year_specific(
    ndb_stub, test_data_importer
) -> None:
    """
    From 2017 on the qual/playoff high scores subtract foul points while the
    overall high score keeps them, and the year's game insights are attached
    both per week and for the season.
    """
    test_data_importer.import_event(__file__, "data/2019nyny.json")
    test_data_importer.import_match_list(__file__, "data/2019nyny_matches.json")
    with open(
        test_data_importer._get_path(__file__, "data/2019nyny_insights.json"), "r"
    ) as f:
        expected_event_insights = json.load(f)
    with open(
        test_data_importer._get_path(__file__, "data/2019nyny_matches.json"), "r"
    ) as f:
        raw_matches = json.load(f)
    overall_highscore = max(
        max(m["alliances"]["red"]["score"], m["alliances"]["blue"]["score"])
        for m in raw_matches
    )

    insights = InsightsHelper.doMatchInsights(2019)
    by_name = _insights_by_name(insights)

    highscore = by_name[Insight.INSIGHT_NAMES[Insight.MATCH_HIGHSCORE]].data
    # Penalty-free leaders match the clean-score leaderboard for this event
    assert _match_keys(highscore["qual"]) == {"2019nyny_qm57"}
    assert _match_keys(highscore["playoff"]) == {"2019nyny_f1m1", "2019nyny_qf1m1"}
    assert all(
        max(m["alliances"]["red"]["score"], m["alliances"]["blue"]["score"])
        == overall_highscore
        for m in highscore["overall"]
    )

    assert (
        by_name[Insight.INSIGHT_NAMES[Insight.YEAR_SPECIFIC]].data
        == expected_event_insights
    )
    assert by_name[Insight.INSIGHT_NAMES[Insight.YEAR_SPECIFIC_BY_WEEK]].data == [
        ["Week 1", expected_event_insights]
    ]


def test_do_award_insights_computes_all_award_stats(ndb_stub) -> None:
    _put_event("2024cmptx", EventType.CMP_FINALS, datetime.datetime(2024, 4, 17))
    _put_event("2024cmpmi", EventType.CMP_FINALS, datetime.datetime(2024, 4, 24))
    _put_event("2024arc", EventType.CMP_DIVISION, datetime.datetime(2024, 4, 17))
    _put_event("2024nyny", EventType.REGIONAL, datetime.datetime(2024, 3, 7))
    _put_event("2024nyro", EventType.REGIONAL, datetime.datetime(2024, 3, 14))
    _put_event("2024necmp", EventType.DISTRICT_CMP, datetime.datetime(2024, 4, 3))
    _put_event("2024ned", EventType.DISTRICT, datetime.datetime(2024, 3, 21))
    _put_event("2024off", EventType.OFFSEASON, datetime.datetime(2024, 7, 1))

    einstein = ["frc254", "frc1678", "frc2910"]
    _put_award("2024cmptx", AwardType.WINNER, einstein, EventType.CMP_FINALS)
    _put_award("2024cmptx", AwardType.FINALIST, ["frc118"], EventType.CMP_FINALS)
    _put_award("2024cmptx", AwardType.CHAIRMANS, ["frc321"], EventType.CMP_FINALS)
    _put_award("2024cmptx", AwardType.WOODIE_FLOWERS, ["frc999"], EventType.CMP_FINALS)
    # A second Championship's WFA banner is not counted (Award.count_banner)
    _put_award("2024cmpmi", AwardType.WOODIE_FLOWERS, ["frc999"], EventType.CMP_FINALS)
    _put_award("2024arc", AwardType.WINNER, einstein, EventType.CMP_DIVISION)
    _put_award("2024arc", AwardType.FINALIST, ["frc118"], EventType.CMP_DIVISION)
    _put_award(
        "2024nyny", AwardType.WINNER, ["frc1", "frc2", "frc3"], EventType.REGIONAL
    )
    _put_award("2024nyny", AwardType.CHAIRMANS, ["frc10"], EventType.REGIONAL)
    _put_award(
        "2024nyny", AwardType.ENGINEERING_INSPIRATION, ["frc20"], EventType.REGIONAL
    )
    _put_award(
        "2024nyro", AwardType.WINNER, ["frc1", "frc2", "frc4"], EventType.REGIONAL
    )
    _put_award("2024nyro", AwardType.CHAIRMANS, ["frc10"], EventType.REGIONAL)
    _put_award(
        "2024necmp",
        AwardType.WINNER,
        ["frc40", "frc41", "frc42"],
        EventType.DISTRICT_CMP,
    )
    _put_award("2024necmp", AwardType.CHAIRMANS, ["frc30"], EventType.DISTRICT_CMP)
    _put_award(
        "2024ned", AwardType.WINNER, ["frc40", "frc41", "frc43"], EventType.DISTRICT
    )
    # District-event Chairman's is a banner but not a "regional" Chairman's
    _put_award("2024ned", AwardType.CHAIRMANS, ["frc50"], EventType.DISTRICT)
    # Offseason events are not season events and are ignored entirely
    _put_award("2024off", AwardType.WINNER, ["frc77"], EventType.OFFSEASON)

    insights = InsightsHelper.doAwardInsights(2024)
    by_name = _insights_by_name(insights)

    assert set(by_name.keys()) == {
        Insight.INSIGHT_NAMES[Insight.BLUE_BANNERS],
        Insight.INSIGHT_NAMES[Insight.CA_WINNER],
        Insight.INSIGHT_NAMES[Insight.WORLD_CHAMPIONS],
        Insight.INSIGHT_NAMES[Insight.WORLD_FINALISTS],
        Insight.INSIGHT_NAMES[Insight.DIVISION_WINNERS],
        Insight.INSIGHT_NAMES[Insight.DIVISION_FINALISTS],
        Insight.INSIGHT_NAMES[Insight.RCA_WINNERS],
        Insight.INSIGHT_NAMES[Insight.REGIONAL_DISTRICT_WINNERS],
        Insight.INSIGHT_NAMES[Insight.SUCCESSFUL_ELIM_TEAMUPS],
        Insight.INSIGHT_NAMES[Insight.SUCCESSFUL_EINSTEIN_TEAMUPS],
    }
    for insight in insights:
        assert insight.year == 2024
        assert insight.district_abbreviation is None

    assert by_name[Insight.INSIGHT_NAMES[Insight.BLUE_BANNERS]].data == [
        [
            2,
            ["frc1", "frc2", "frc10", "frc40", "frc41", "frc254", "frc1678", "frc2910"],
        ],
        [1, ["frc3", "frc4", "frc30", "frc42", "frc43", "frc50", "frc321", "frc999"]],
    ]
    assert by_name[Insight.INSIGHT_NAMES[Insight.CA_WINNER]].data == "frc321"
    assert by_name[Insight.INSIGHT_NAMES[Insight.WORLD_CHAMPIONS]].data == einstein
    assert by_name[Insight.INSIGHT_NAMES[Insight.WORLD_FINALISTS]].data == ["frc118"]
    assert by_name[Insight.INSIGHT_NAMES[Insight.DIVISION_WINNERS]].data == einstein
    assert by_name[Insight.INSIGHT_NAMES[Insight.DIVISION_FINALISTS]].data == ["frc118"]
    # One entry per Chairman's win at a regional or district championship
    assert by_name[Insight.INSIGHT_NAMES[Insight.RCA_WINNERS]].data == [
        "frc10",
        "frc10",
        "frc30",
    ]
    assert by_name[Insight.INSIGHT_NAMES[Insight.REGIONAL_DISTRICT_WINNERS]].data == [
        [2, ["frc1", "frc2", "frc40", "frc41"]],
        [1, ["frc3", "frc4", "frc42", "frc43"]],
    ]
    elim_teamups = by_name[Insight.INSIGHT_NAMES[Insight.SUCCESSFUL_ELIM_TEAMUPS]].data
    assert sorted(elim_teamups) == sorted(
        [
            einstein,
            einstein,
            ["frc1", "frc2", "frc3"],
            ["frc1", "frc2", "frc4"],
            ["frc40", "frc41", "frc42"],
            ["frc40", "frc41", "frc43"],
        ]
    )
    assert by_name[Insight.INSIGHT_NAMES[Insight.SUCCESSFUL_EINSTEIN_TEAMUPS]].data == [
        einstein
    ]


def test_do_award_insights_with_no_awards_is_empty(ndb_stub) -> None:
    _put_event("2024nyny", EventType.REGIONAL, datetime.datetime(2024, 3, 7))

    assert InsightsHelper.doAwardInsights(2024) == []


def test_do_prediction_insights_counts_championship_events_separately() -> None:
    def fake_match(key: Any, comp_level: str, winner: str) -> SimpleNamespace:
        return SimpleNamespace(
            has_been_played=True,
            comp_level=comp_level,
            key=SimpleNamespace(id=lambda: key),
            winning_alliance=winner,
        )

    cmp_event = SimpleNamespace(
        event_type_enum=EventType.CMP_DIVISION,
        prep_details=mock.Mock(),
        prep_matches=mock.Mock(),
        details=SimpleNamespace(
            predictions={
                "match_predictions": {
                    "qual": {"2024arc_qm1": {"winning_alliance": "red"}},
                    "playoff": {"2024arc_sf1m1": {"winning_alliance": "blue"}},
                },
                "match_prediction_stats": {
                    "qual": {"brier_scores": {"win_loss": 0.25}},
                    "playoff": {"brier_scores": {"win_loss": 0.5}},
                },
            }
        ),
        matches=[
            fake_match("2024arc_qm1", "qm", "red"),
            fake_match("2024arc_sf1m1", "sf", "red"),
            # Non-string keys are skipped after being counted as played
            fake_match(12345, "qm", "red"),
            # Unplayed matches are ignored
            SimpleNamespace(has_been_played=False, comp_level="qm"),
        ],
    )
    regional_event = SimpleNamespace(
        event_type_enum=EventType.REGIONAL,
        prep_details=mock.Mock(),
        prep_matches=mock.Mock(),
        details=SimpleNamespace(
            predictions={
                "match_predictions": {
                    "qual": {"2024nyny_qm1": {"winning_alliance": "blue"}},
                    "playoff": {},
                },
                "match_prediction_stats": {
                    "qual": {"brier_scores": {"win_loss": 0.75}},
                    # No playoff brier score recorded
                    "playoff": {},
                },
            }
        ),
        matches=[fake_match("2024nyny_qm1", "qm", "blue")],
    )
    # Events without details, or without predictions, contribute nothing
    no_details_event = SimpleNamespace(
        event_type_enum=EventType.REGIONAL,
        prep_details=mock.Mock(),
        prep_matches=mock.Mock(),
        details=None,
        matches=[],
    )
    no_predictions_event = SimpleNamespace(
        event_type_enum=EventType.REGIONAL,
        prep_details=mock.Mock(),
        prep_matches=mock.Mock(),
        details=SimpleNamespace(predictions=None),
        matches=[fake_match("2024nyro_qm1", "qm", "red")],
    )

    insights = InsightsHelper._doPredictionInsightsForEvents(
        year=2024,
        events=cast(
            List[Event],
            [cmp_event, regional_event, no_details_event, no_predictions_event],
        ),
    )

    assert len(insights) == 1
    assert insights[0].district_abbreviation is None
    assert insights[0].data == {
        "qual": {
            "mean_brier_score": 0.5,
            "correct_matches_count": 2,
            "total_matches_count": 3,
            "mean_brier_score_cmp": 0.25,
            "correct_matches_count_cmp": 1,
            "total_matches_count_cmp": 2,
        },
        "playoff": {
            "mean_brier_score": 0.5,
            "correct_matches_count": 0,
            "total_matches_count": 1,
            "mean_brier_score_cmp": 0.5,
            "correct_matches_count_cmp": 0,
            "total_matches_count_cmp": 1,
        },
    }


def test_do_overall_award_insights_aggregates_every_yearly_insight(ndb_stub) -> None:
    for year, champions in [
        (2022, ["frc254", "frc1"]),
        (2023, ["frc254", "frc2"]),
        (2024, ["frc3"]),
    ]:
        create_insight(
            data=champions,
            name=Insight.INSIGHT_NAMES[Insight.WORLD_CHAMPIONS],
            year=year,
        ).put()
        create_insight(
            data=[champions],
            name=Insight.INSIGHT_NAMES[Insight.SUCCESSFUL_EINSTEIN_TEAMUPS],
            year=year,
        ).put()
    for year, winners in [
        (2019, ["frc254", "frc1"]),
        (2022, ["frc254"]),
        (2023, ["frc254", "frc2"]),
        (2024, ["frc2"]),
    ]:
        create_insight(
            data=winners,
            name=Insight.INSIGHT_NAMES[Insight.DIVISION_WINNERS],
            year=year,
        ).put()
    create_insight(
        data=[(2, ["frc254"]), (1, ["frc1"])],
        name=Insight.INSIGHT_NAMES[Insight.REGIONAL_DISTRICT_WINNERS],
        year=2024,
    ).put()
    create_insight(
        data=[(3, ["frc254"])],
        name=Insight.INSIGHT_NAMES[Insight.BLUE_BANNERS],
        year=2024,
    ).put()
    create_insight(
        data=["frc254", "frc1"],
        name=Insight.INSIGHT_NAMES[Insight.RCA_WINNERS],
        year=2024,
    ).put()
    create_insight(
        data=[["frc254", "frc1", "frc2"]],
        name=Insight.INSIGHT_NAMES[Insight.SUCCESSFUL_ELIM_TEAMUPS],
        year=2024,
    ).put()

    insights = InsightsHelper.doOverallAwardInsights()
    by_name = _insights_by_name(insights)

    for insight in insights:
        assert insight.year == 0
        assert insight.district_abbreviation is None

    assert by_name[Insight.INSIGHT_NAMES[Insight.REGIONAL_DISTRICT_WINNERS]].data == [
        [2, ["frc254"]],
        [1, ["frc1"]],
    ]
    assert by_name[Insight.INSIGHT_NAMES[Insight.BLUE_BANNERS]].data == [
        [3, ["frc254"]]
    ]
    assert by_name[Insight.INSIGHT_NAMES[Insight.RCA_WINNERS]].data == [
        [1, ["frc1", "frc254"]]
    ]
    # Grouped by number of titles, then by team number, with sorted years
    assert by_name[Insight.INSIGHT_NAMES[Insight.WORLD_CHAMPIONS]].data == [
        [2, [["frc254", [2022, 2023]]]],
        [1, [["frc1", [2022]], ["frc2", [2023]], ["frc3", [2024]]]],
    ]
    assert by_name[Insight.INSIGHT_NAMES[Insight.DIVISION_WINNERS]].data == [
        [3, [["frc254", [2019, 2022, 2023]]]],
        [2, [["frc2", [2023, 2024]]]],
        [1, [["frc1", [2019]]]],
    ]
    # 2019 -> 2022 bridges the COVID gap
    assert by_name[Insight.INSIGHT_NAMES[Insight.EINSTEIN_STREAK]].data == [
        [3, ["frc254"]],
        [2, ["frc2"]],
        [1, ["frc1"]],
    ]
    # Pairs within a win-count group keep discovery order, so compare as sets
    elim_teamups = by_name[Insight.INSIGHT_NAMES[Insight.SUCCESSFUL_ELIM_TEAMUPS]].data
    assert [count for count, _ in elim_teamups] == [1]
    assert sorted(elim_teamups[0][1]) == [
        ["frc1", "frc2"],
        ["frc1", "frc254"],
        ["frc2", "frc254"],
    ]
    einstein_teamups = by_name[
        Insight.INSIGHT_NAMES[Insight.SUCCESSFUL_EINSTEIN_TEAMUPS]
    ].data
    assert [count for count, _ in einstein_teamups] == [1]
    assert sorted(einstein_teamups[0][1]) == [["frc1", "frc254"], ["frc2", "frc254"]]


def test_do_overall_award_insights_with_nothing_stored_is_empty(ndb_stub) -> None:
    assert InsightsHelper.doOverallAwardInsights() == []


def test_do_overall_match_insights_with_nothing_stored_is_empty(ndb_stub) -> None:
    assert InsightsHelper.doOverallMatchInsights() == []


def test_bug_17_no_prediction_insight_without_predictions() -> None:
    """Bug #17: a zero-count MATCH_PREDICTIONS insight is emitted anyway.

    Today _doPredictionInsightsForEvents sets `data = None` when no event had
    predictions, but the next line overwrites it with defaultdict(dict), so
    an insight with all-zero counts and None Brier scores is emitted.
    Correct: with no predictions, no insight is emitted.
    """
    insights = InsightsHelper._doPredictionInsightsForEvents(year=2024, events=[])

    assert insights == []
