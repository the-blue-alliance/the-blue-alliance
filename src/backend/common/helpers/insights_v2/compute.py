from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Dict, List, Optional

from google.appengine.ext import ndb

from backend.common.consts.event_type import SEASON_EVENT_TYPES
from backend.common.helpers.season_helper import SeasonHelper
from backend.common.models.event import Event
from backend.common.models.insight_v2 import InsightV2, LeaderboardRankingV2
from backend.common.models.keys import Year
from backend.common.queries.event_query import EventListQuery

LEADERBOARD_TOP_N = 25


def build_leaderboard_rankings(
    counts: Dict[str, int], top_n: int = LEADERBOARD_TOP_N
) -> List[LeaderboardRankingV2]:
    """
    Converts a {team_key: count} dict into a sorted list of LeaderboardRankingV2,
    grouping keys with equal counts and sorting descending by value.
    Teams within a group are sorted numerically by team number.
    """
    value_to_keys: Dict[int, List[str]] = defaultdict(list)
    for key, count in counts.items():
        value_to_keys[count].append(key)

    return [
        LeaderboardRankingV2(
            keys=sorted(keys, key=lambda k: int(k[3:])),
            value=value,
        )
        for value, keys in sorted(value_to_keys.items(), reverse=True)
    ][:top_n]


class InsightV2Calculator(ABC):
    @abstractmethod
    def on_event(self, event: Event) -> None: ...

    @abstractmethod
    def make_insight(self, year: Year) -> Optional[InsightV2]: ...


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
            for calc in calculators:
                calc.on_event(event)
            event.clear_awards()
            ndb.get_context().clear_cache()

    insights = []
    for calc in calculators:
        if insight := calc.make_insight(year):
            insights.append(insight)
    return insights
