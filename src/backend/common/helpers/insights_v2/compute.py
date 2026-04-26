from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Any, DefaultDict, Dict, Iterable, List, Optional, Set, Tuple

from google.appengine.ext import ndb

from backend.common.consts.event_type import SEASON_EVENT_TYPES
from backend.common.consts.renamed_districts import RenamedDistricts
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
from backend.common.queries.district_query import AllDistrictTeamsQuery
from backend.common.queries.event_query import EventListQuery

LEADERBOARD_TOP_N = 25
LEADERBOARD_MAX_KEYS_PER_RANKING = 10


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
        if value > 1 and len(keys) <= LEADERBOARD_MAX_KEYS_PER_RANKING
    ][:top_n]


def build_leaderboard_pair_rankings(
    counts: Dict[str, int], top_n: int = LEADERBOARD_TOP_N
) -> List[LeaderboardRankingV2]:
    """
    Converts a {"frcA|frcB": count} dict into a sorted list of LeaderboardRankingV2.
    Pairs with equal counts are grouped into one entry (mirroring build_leaderboard_rankings).
    keys is List[List[str]]; each inner list is [team_a, team_b].
    """
    value_to_pairs: Dict[int, List[List[str]]] = defaultdict(list)
    for key, count in counts.items():
        value_to_pairs[count].append(key.split("|"))

    def _pair_sort_key(pair: List[str]) -> Tuple[int, int]:
        return (int(pair[0][3:]), int(pair[1][3:]))

    return [
        LeaderboardRankingV2(
            keys=sorted(pairs, key=_pair_sort_key),
            value=value,
        )
        for value, pairs in sorted(value_to_pairs.items(), reverse=True)
        if value > 1 and len(pairs) <= LEADERBOARD_MAX_KEYS_PER_RANKING
    ][:top_n]


def _build_team_district_map(team_keys: Iterable[str]) -> Dict[str, str]:
    """
    Returns {team_key: district_abbrev} for the given team keys, using each
    team's most recent district membership. Fetches all DistrictTeam records in
    one query and filters in memory.
    """
    team_keys_set = set(team_keys)
    all_district_teams = AllDistrictTeamsQuery().fetch()

    team_district_teams: Dict[str, List[Any]] = defaultdict(list)
    for dt in all_district_teams:
        if dt.team and str(dt.team.id()) in team_keys_set:
            team_district_teams[str(dt.team.id())].append(dt)

    return {
        team_key: RenamedDistricts.get_latest_code(
            str(max(dts, key=lambda dt: dt.year).district_key.id())[4:]
        )
        for team_key, dts in team_district_teams.items()
    }


class InsightV2Calculator(ABC):
    @property
    def team_keys(self) -> Set[str]:
        return set()

    @abstractmethod
    def on_event(self, event: Event) -> None: ...

    @abstractmethod
    def make_insights(
        self, year: Year, team_to_district: Dict[str, str]
    ) -> List[InsightV2]: ...


class LeaderboardV2Calculator(InsightV2Calculator, ABC):
    def __init__(self) -> None:
        self.counts: Dict[str, int] = defaultdict(int)

    @property
    def team_keys(self) -> Set[str]:
        return set(self.counts.keys())

    @property
    @abstractmethod
    def insight_name(self) -> InsightV2NameEntry: ...

    @property
    @abstractmethod
    def key_type(self) -> LeaderboardKeyType: ...

    @abstractmethod
    def _build_rankings(self, counts: Dict[str, int]) -> List[LeaderboardRankingV2]:
        # Each leaderboard type controls how its counts are turned into rankings
        # (e.g. single-string keys vs. compound pair keys have different sort/grouping
        # logic and produce different keys shapes in the output).
        ...

    def _get_district(
        self, key: str, team_to_district: Dict[str, str]
    ) -> Optional[str]:
        # Default: the count key IS the team key, so district lookup is direct.
        # Override when a key encodes multiple teams (e.g. a pair), where the
        # district should only be assigned if all teams share the same district.
        return team_to_district.get(key)

    def _increment(self, key: str, count: int = 1) -> None:
        self.counts[key] += count

    def make_insights(
        self, year: Year, team_to_district: Dict[str, str]
    ) -> List[InsightV2]:
        district_counts: DefaultDict[str, DefaultDict[str, int]] = defaultdict(
            lambda: defaultdict(int)
        )
        for key, count in self.counts.items():
            if district := self._get_district(key, team_to_district):
                district_counts[district][key] += count

        insights = []

        if self.counts:
            data = LeaderboardDataV2(
                rankings=self._build_rankings(self.counts),
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

        for district_abbrev, counts in sorted(district_counts.items()):
            if not counts:
                continue
            data = LeaderboardDataV2(
                rankings=self._build_rankings(counts),
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
            event.prep_matches()
            for calc in calculators:
                calc.on_event(event)
            event.clear_awards()
            event.clear_matches()
            ndb.get_context().clear_cache()

    all_team_keys: Set[str] = set()
    for calc in calculators:
        all_team_keys.update(calc.team_keys)
    team_to_district = _build_team_district_map(all_team_keys)

    insights = []
    for calc in calculators:
        insights.extend(calc.make_insights(year, team_to_district))
    return insights
