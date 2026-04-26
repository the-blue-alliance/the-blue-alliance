from abc import abstractmethod
from collections import defaultdict
from typing import DefaultDict, Dict, List, Optional, Tuple

from backend.common.helpers.insights_v2.base import InsightV2Calculator
from backend.common.helpers.insights_v2.names import InsightV2NameEntry
from backend.common.models.insight_v2 import (
    EventListContext,
    InsightCategory,
    InsightV2,
    LeaderboardContextType,
    LeaderboardDataV2,
    LeaderboardKeyType,
    LeaderboardRanking,
    LeaderboardRankingV2,
    LeaderboardRankingWithEventList,
)
from backend.common.models.keys import Year

LEADERBOARD_TOP_N = 25
LEADERBOARD_MAX_KEYS_PER_RANKING = 10


def build_leaderboard_rankings(
    counts: Dict[str, int], top_n: int = LEADERBOARD_TOP_N
) -> List[LeaderboardRanking]:
    """
    Converts a {team_key: count} dict into a sorted list of LeaderboardRankingV2,
    grouping keys with equal counts and sorting descending by value.
    Teams within a group are sorted numerically by team number.
    """
    value_to_keys: Dict[int, List[str]] = defaultdict(list)
    for key, count in counts.items():
        value_to_keys[count].append(key)

    result: List[LeaderboardRanking] = [
        LeaderboardRankingV2(
            keys=sorted(keys, key=lambda k: int(k[3:])),
            value=value,
        )
        for value, keys in sorted(value_to_keys.items(), reverse=True)
        if value > 1 and len(keys) <= LEADERBOARD_MAX_KEYS_PER_RANKING
    ]
    return result[:top_n]


def build_leaderboard_event_list_rankings(
    team_events: Dict[str, List[str]], top_n: int = LEADERBOARD_TOP_N
) -> List[LeaderboardRanking]:
    """
    Converts a {team_key: [event_key, ...]} dict into a sorted list of
    LeaderboardRankingWithEventList. Teams with the same count are grouped;
    contexts is a per-team list parallel to keys.
    """
    counts_to_teams: DefaultDict[int, List[str]] = defaultdict(list)
    for team_key, events in team_events.items():
        if events:
            counts_to_teams[len(events)].append(team_key)

    result: List[LeaderboardRanking] = []
    for count, team_keys in sorted(counts_to_teams.items(), reverse=True):
        if count <= 1:
            continue
        if len(team_keys) > LEADERBOARD_MAX_KEYS_PER_RANKING:
            continue
        sorted_keys = sorted(team_keys, key=lambda k: int(k[3:]))
        result.append(
            LeaderboardRankingWithEventList(
                keys=sorted_keys,
                value=count,
                contexts=[
                    EventListContext(event_keys=sorted(team_events[tk]))
                    for tk in sorted_keys
                ],
            )
        )
    return result[:top_n]


def build_leaderboard_pair_rankings(
    counts: Dict[str, int], top_n: int = LEADERBOARD_TOP_N
) -> List[LeaderboardRanking]:
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

    result: List[LeaderboardRanking] = [
        LeaderboardRankingV2(
            keys=sorted(pairs, key=_pair_sort_key),
            value=value,
        )
        for value, pairs in sorted(value_to_pairs.items(), reverse=True)
        if value > 1 and len(pairs) <= LEADERBOARD_MAX_KEYS_PER_RANKING
    ]
    return result[:top_n]


class LeaderboardV2Calculator(InsightV2Calculator):
    def __init__(self) -> None:
        self.counts: Dict[str, int] = defaultdict(int)

    @property
    @abstractmethod
    def insight_name(self) -> InsightV2NameEntry: ...

    @property
    @abstractmethod
    def key_type(self) -> LeaderboardKeyType: ...

    @property
    def context_type(self) -> LeaderboardContextType:
        return "none"

    @abstractmethod
    def _build_rankings(self, counts: Dict[str, int]) -> List[LeaderboardRanking]:
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
                context_type=self.context_type,
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
                context_type=self.context_type,
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


class EventListLeaderboardV2Calculator(LeaderboardV2Calculator):
    """
    Base class for leaderboards that track per-team event lists alongside counts.
    Rankings include a context.event_keys field listing the events where each
    group of teams achieved the milestone.
    """

    def __init__(self) -> None:
        super().__init__()
        self._team_events: DefaultDict[str, List[str]] = defaultdict(list)

    @property
    def context_type(self) -> LeaderboardContextType:
        return "event_list"

    def _record_event(self, team_key: str, event_key: str) -> None:
        if event_key not in self._team_events[team_key]:
            self._increment(team_key)
            self._team_events[team_key].append(event_key)

    def _build_rankings(self, counts: Dict[str, int]) -> List[LeaderboardRanking]:
        filtered = {k: self._team_events[k] for k in counts}
        return build_leaderboard_event_list_rankings(filtered)
