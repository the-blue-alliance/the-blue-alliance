from typing import Dict, List

from backend.common.helpers.insights_v2.leaderboards.calculator import (
    build_leaderboard_rankings,
    LeaderboardV2Calculator,
)
from backend.common.helpers.insights_v2.names import InsightV2NameEntry, InsightV2Names
from backend.common.models.event import Event
from backend.common.models.insight_v2 import LeaderboardKeyType, LeaderboardRanking


class MostMatchesPlayedV2Calculator(LeaderboardV2Calculator):
    @property
    def insight_name(self) -> InsightV2NameEntry:
        return InsightV2Names.MOST_MATCHES_PLAYED

    @property
    def key_type(self) -> LeaderboardKeyType:
        return "team"

    def _build_rankings(self, counts: Dict[str, int]) -> List[LeaderboardRanking]:
        return build_leaderboard_rankings(counts, min_count=self.min_count)

    def on_event(self, event: Event) -> None:
        for match in event.matches:
            if match.has_been_played:
                for team_key in match.team_key_names:
                    self._increment(team_key)
