from typing import Dict, List

from backend.common.helpers.insights_v2.leaderboards.calculator import (
    build_leaderboard_rankings,
    LeaderboardV2Calculator,
)
from backend.common.helpers.insights_v2.names import InsightV2NameEntry, InsightV2Names
from backend.common.models.event import Event
from backend.common.models.insight_v2 import LeaderboardKeyType, LeaderboardRanking


class MostAwardsWonV2Calculator(LeaderboardV2Calculator):
    @property
    def insight_name(self) -> InsightV2NameEntry:
        return InsightV2Names.MOST_AWARDS_WON

    @property
    def key_type(self) -> LeaderboardKeyType:
        return "team"

    @property
    def min_count(self) -> int:
        return 2

    def _build_rankings(self, counts: Dict[str, int]) -> List[LeaderboardRanking]:
        return build_leaderboard_rankings(counts, min_count=self.min_count)

    def on_event(self, event: Event) -> None:
        for award in event.awards:
            for team_key in award.team_list:
                self._increment(str(team_key.id()))
