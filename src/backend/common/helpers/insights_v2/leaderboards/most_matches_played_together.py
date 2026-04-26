import itertools
from typing import Dict, List, Optional, Set

from backend.common.helpers.insights_v2.leaderboards.calculator import (
    build_leaderboard_pair_rankings,
    LeaderboardV2Calculator,
)
from backend.common.helpers.insights_v2.names import InsightV2NameEntry, InsightV2Names
from backend.common.models.event import Event
from backend.common.models.insight_v2 import LeaderboardKeyType, LeaderboardRankingV2


class MostMatchesPlayedTogetherV2Calculator(LeaderboardV2Calculator):
    @property
    def insight_name(self) -> InsightV2NameEntry:
        return InsightV2Names.MOST_MATCHES_PLAYED_TOGETHER

    @property
    def key_type(self) -> LeaderboardKeyType:
        return "team_pair"

    @property
    def team_keys(self) -> Set[str]:
        keys: Set[str] = set()
        for pair_key in self.counts:
            team_a, team_b = pair_key.split("|")
            keys.add(team_a)
            keys.add(team_b)
        return keys

    def _build_rankings(self, counts: Dict[str, int]) -> List[LeaderboardRankingV2]:
        return build_leaderboard_pair_rankings(counts)

    def _get_district(
        self, key: str, team_to_district: Dict[str, str]
    ) -> Optional[str]:
        team_a, team_b = key.split("|")
        district_a = team_to_district.get(team_a)
        district_b = team_to_district.get(team_b)
        return district_a if district_a and district_a == district_b else None

    def on_event(self, event: Event) -> None:
        for match in event.matches:
            if not match.has_been_played:
                continue
            for alliance in match.alliances.values():
                teams = alliance["teams"]
                for team_a, team_b in itertools.combinations(teams, 2):
                    pair = sorted([team_a, team_b], key=lambda k: int(k[3:]))
                    self._increment(f"{pair[0]}|{pair[1]}")
