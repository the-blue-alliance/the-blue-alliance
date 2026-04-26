from collections import defaultdict
from typing import Any, Dict, List

from google.appengine.ext import ndb

from backend.common.consts.event_type import SEASON_EVENT_TYPES
from backend.common.consts.renamed_districts import RenamedDistricts
from backend.common.helpers.insights_v2.base import InsightV2Calculator
from backend.common.helpers.insights_v2.leaderboards.blue_banners import (
    BlueBannersV2Calculator,
)
from backend.common.helpers.insights_v2.leaderboards.most_cmp_finals_appearances import (
    MostCmpFinalsAppearancesV2Calculator,
)
from backend.common.helpers.insights_v2.leaderboards.most_cmp_wins import (
    MostCmpWinsV2Calculator,
)
from backend.common.helpers.insights_v2.leaderboards.most_division_finals_appearances import (
    MostDivisionFinalsAppearancesV2Calculator,
)
from backend.common.helpers.insights_v2.leaderboards.most_division_wins import (
    MostDivisionWinsV2Calculator,
)
from backend.common.helpers.insights_v2.leaderboards.most_matches_played import (
    MostMatchesPlayedV2Calculator,
)
from backend.common.helpers.insights_v2.leaderboards.most_matches_played_together import (
    MostMatchesPlayedTogetherV2Calculator,
)
from backend.common.helpers.insights_v2.streaks.einstein_streak import (
    LongestEinsteinStreakV2Calculator,
)
from backend.common.helpers.insights_v2.streaks.qualifying_event_streak import (
    LongestQualifyingEventStreakV2Calculator,
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
        for event in EventListQuery(year=event_year).fetch():
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
        MostDivisionFinalsAppearancesV2Calculator(),
        MostDivisionWinsV2Calculator(),
        MostCmpFinalsAppearancesV2Calculator(),
        MostCmpWinsV2Calculator(),
    ]
    if year == 0:
        calculators += [
            LongestQualifyingEventStreakV2Calculator(),
            LongestEinsteinStreakV2Calculator(),
        ]
    return compute_insights_for_year(year, calculators)
