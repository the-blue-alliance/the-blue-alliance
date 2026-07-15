from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List

from google.appengine.ext import ndb

from backend.common.consts.event_type import SEASON_EVENT_TYPES
from backend.common.consts.renamed_districts import RenamedDistricts
from backend.common.helpers.insights_v2.base import InsightV2Calculator
from backend.common.helpers.insights_v2.leaderboards.blue_banners import (
    BlueBannersV2Calculator,
)
from backend.common.helpers.insights_v2.leaderboards.highest_auto_score import (
    HighestAutoScoreV2Calculator,
)
from backend.common.helpers.insights_v2.leaderboards.highest_endgame_score import (
    HighestEndgameScoreV2Calculator,
)
from backend.common.helpers.insights_v2.leaderboards.highest_losing_score import (
    HighestLosingScoreV2Calculator,
)
from backend.common.helpers.insights_v2.leaderboards.highest_match_clean_combined_score import (
    HighestMatchCleanCombinedScoreV2Calculator,
)
from backend.common.helpers.insights_v2.leaderboards.highest_match_clean_score import (
    HighestMatchCleanScoreV2Calculator,
)
from backend.common.helpers.insights_v2.leaderboards.highest_teleop_score import (
    HighestTeleopScoreV2Calculator,
)
from backend.common.helpers.insights_v2.leaderboards.most_awards_won import (
    MostAwardsWonV2Calculator,
)
from backend.common.helpers.insights_v2.leaderboards.most_cmp_finals_appearances import (
    MostCmpFinalsAppearancesV2Calculator,
)
from backend.common.helpers.insights_v2.leaderboards.most_cmp_wins import (
    MostCmpWinsV2Calculator,
)
from backend.common.helpers.insights_v2.leaderboards.most_district_cmp_wins import (
    MostDistrictCmpWinsV2Calculator,
)
from backend.common.helpers.insights_v2.leaderboards.most_division_finals_appearances import (
    MostDivisionFinalsAppearancesV2Calculator,
)
from backend.common.helpers.insights_v2.leaderboards.most_division_wins import (
    MostDivisionWinsV2Calculator,
)
from backend.common.helpers.insights_v2.leaderboards.most_events_won import (
    MostEventsWonV2Calculator,
)
from backend.common.helpers.insights_v2.leaderboards.most_events_won_together import (
    MostEventsWonTogetherV2Calculator,
)
from backend.common.helpers.insights_v2.leaderboards.most_game_pieces_scored import (
    MostGamePiecesScoredV2Calculator,
)
from backend.common.helpers.insights_v2.leaderboards.most_impact_award_wins import (
    MostImpactAwardWinsV2Calculator,
)
from backend.common.helpers.insights_v2.leaderboards.most_matches_played import (
    MostMatchesPlayedV2Calculator,
)
from backend.common.helpers.insights_v2.leaderboards.most_matches_played_together import (
    MostMatchesPlayedTogetherV2Calculator,
)
from backend.common.helpers.insights_v2.leaderboards.most_wffa_wins import (
    MostWffaWinsV2Calculator,
)
from backend.common.helpers.insights_v2.streaks.einstein_streak import (
    LongestEinsteinStreakV2Calculator,
)
from backend.common.helpers.insights_v2.streaks.qualifying_event_streak import (
    LongestQualifyingEventStreakV2Calculator,
)
from backend.common.helpers.insights_v2.streaks.undefeated_streak import (
    LongestUndefeatedStreakV2Calculator,
)
from backend.common.helpers.insights_v2.streaks.win_streak import (
    LongestWinStreakV2Calculator,
)
from backend.common.helpers.insights_v2.timeseries.average_match_score_by_week import (
    AverageMatchScoreByWeekV2Calculator,
)
from backend.common.helpers.insights_v2.timeseries.average_win_margin_by_week import (
    AverageWinMarginByWeekV2Calculator,
)
from backend.common.helpers.insights_v2.timeseries.high_score_over_time import (
    HighScoreOverTimeV2Calculator,
)
from backend.common.helpers.season_helper import SeasonHelper
from backend.common.models.insight_v2 import InsightV2
from backend.common.models.keys import Year
from backend.common.queries.district_query import AllDistrictTeamsQuery
from backend.common.queries.event_query import EventListQuery


def _build_team_district_map() -> Dict[str, str]:
    """
    Returns {team_key: district_abbrev} for all teams, using each team's most
    recent district membership.
    """
    all_district_teams = AllDistrictTeamsQuery().fetch()

    team_district_teams: Dict[str, List[Any]] = defaultdict(list)
    for dt in all_district_teams:
        if dt.team:
            team_district_teams[str(dt.team.id())].append(dt)

    return {
        team_key: RenamedDistricts.get_latest_code(
            str(max(dts, key=lambda dt: dt.year).district_key.id())[4:]
        )
        for team_key, dts in team_district_teams.items()
    }


def compute_insights_for_year(
    year: Year, calculators: List[InsightV2Calculator]
) -> List[InsightV2]:
    """
    Iterates over all season events for a year (or all years if year=0),
    calling on_event() on every calculator once per event. Preps and clears
    event relations per-event so memory stays bounded.
    """
    event_years = [year] if year != 0 else SeasonHelper.get_valid_years()
    for event_year in event_years:
        events = sorted(
            EventListQuery(year=event_year).fetch(),
            key=lambda e: (e.start_date or datetime(1, 1, 1), e.key_name),
        )
        for event in events:
            if event.event_type_enum not in SEASON_EVENT_TYPES:
                continue

            event.prep_awards()
            event.prep_matches()
            for calc in calculators:
                calc.on_event(event)
            event.clear_awards()
            event.clear_matches()
            ndb.get_context().clear_cache()

    team_to_district = _build_team_district_map()

    insights = []
    for calc in calculators:
        insights.extend(calc.make_insights(year, team_to_district))
    return insights


def make_all_insights(year: Year) -> List[InsightV2]:
    calculators: List[InsightV2Calculator] = [
        BlueBannersV2Calculator(),
        MostMatchesPlayedV2Calculator(),
        MostMatchesPlayedTogetherV2Calculator(),
        MostEventsWonV2Calculator(),
        MostEventsWonTogetherV2Calculator(),
        MostImpactAwardWinsV2Calculator(),
        MostAwardsWonV2Calculator(),
        MostWffaWinsV2Calculator(),
    ]
    if year == 0:
        calculators += [
            MostDistrictCmpWinsV2Calculator(),
            MostDivisionFinalsAppearancesV2Calculator(),
            MostDivisionWinsV2Calculator(),
            MostCmpFinalsAppearancesV2Calculator(),
            MostCmpWinsV2Calculator(),
            LongestQualifyingEventStreakV2Calculator(),
            LongestEinsteinStreakV2Calculator(),
            LongestUndefeatedStreakV2Calculator(),
            LongestWinStreakV2Calculator(),
        ]
    else:
        calculators += [
            HighScoreOverTimeV2Calculator(),
            AverageMatchScoreByWeekV2Calculator(),
            AverageWinMarginByWeekV2Calculator(),
            HighestMatchCleanScoreV2Calculator(),
            HighestMatchCleanCombinedScoreV2Calculator(),
            HighestLosingScoreV2Calculator(),
            HighestAutoScoreV2Calculator(),
            HighestTeleopScoreV2Calculator(),
        ]
        if year not in {2017, 2018, 2023, 2025}:
            calculators.append(HighestEndgameScoreV2Calculator())
        if year in {2016, 2017, 2019, 2020, 2022, 2023, 2024, 2025, 2026}:
            calculators.append(MostGamePiecesScoredV2Calculator())
    return compute_insights_for_year(year, calculators)
