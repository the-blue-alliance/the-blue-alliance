from abc import ABC, abstractmethod
from collections import defaultdict
from typing import DefaultDict, Dict, List, Optional

from google.appengine.ext import ndb

from backend.common.consts.event_type import SEASON_EVENT_TYPES
from backend.common.helpers.season_helper import SeasonHelper
from backend.common.models.event import Event
from backend.common.models.insight_v2 import (
    InsightCategory,
    InsightV2,
    InsightV2NameEntry,
    LeaderboardDataV2,
    LeaderboardKeyType,
    LeaderboardRankingV2,
)
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
    def make_insights(self, year: Year) -> List[InsightV2]: ...


class LeaderboardV2Calculator(InsightV2Calculator, ABC):
    def __init__(self) -> None:
        self.counts: Dict[str, int] = defaultdict(int)
        self.district_counts: DefaultDict[str, DefaultDict[str, int]] = defaultdict(
            lambda: defaultdict(int)
        )

    @property
    @abstractmethod
    def insight_name(self) -> InsightV2NameEntry: ...

    @property
    @abstractmethod
    def key_type(self) -> LeaderboardKeyType: ...

    def _increment(
        self, key: str, count: int = 1, district: Optional[str] = None
    ) -> None:
        self.counts[key] += count
        if district:
            self.district_counts[district][key] += count

    def make_insights(self, year: Year) -> List[InsightV2]:
        insights = []

        if self.counts:
            data = LeaderboardDataV2(
                rankings=build_leaderboard_rankings(self.counts),
                key_type=self.key_type,
            )
            insights.append(
                InsightV2(
                    id=InsightV2.render_key_name(
                        year,
                        InsightCategory.LEADERBOARD,
                        self.insight_name.name,
                    ),
                    name=self.insight_name.name,
                    display_name=self.insight_name.display_name,
                    year=year,
                    category=InsightCategory.LEADERBOARD,
                    data_json=data,
                )
            )

        for district_abbrev, counts in sorted(self.district_counts.items()):
            if not counts:
                continue
            data = LeaderboardDataV2(
                rankings=build_leaderboard_rankings(counts),
                key_type=self.key_type,
            )
            insights.append(
                InsightV2(
                    id=InsightV2.render_key_name(
                        year,
                        InsightCategory.LEADERBOARD,
                        self.insight_name.name,
                        district_abbrev,
                    ),
                    name=self.insight_name.name,
                    display_name=self.insight_name.display_name,
                    year=year,
                    category=InsightCategory.LEADERBOARD,
                    district_abbreviation=district_abbrev,
                    data_json=data,
                )
            )

        return insights


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
        insights.extend(calc.make_insights(year))
    return insights
