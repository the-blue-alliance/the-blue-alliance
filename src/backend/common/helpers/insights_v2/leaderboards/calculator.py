from abc import abstractmethod
from collections import defaultdict
from typing import DefaultDict, Dict, List, Optional, Tuple

from backend.common.helpers.insights_v2.base import InsightV2Calculator
from backend.common.helpers.insights_v2.names import InsightV2NameEntry
from backend.common.models.insight_v2 import (
    InsightCategory,
    InsightV2,
    LeaderboardDataV2,
    LeaderboardKeyType,
    LeaderboardRankingV2,
)
from backend.common.models.keys import Year

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


class LeaderboardV2Calculator(InsightV2Calculator):
    def __init__(self) -> None:
        self.counts: Dict[str, int] = defaultdict(int)

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
