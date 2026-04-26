from typing import Dict, List

from backend.common.consts.award_type import BLUE_BANNER_AWARDS
from backend.common.helpers.insights_v2.leaderboards.calculator import (
    build_leaderboard_rankings,
    LeaderboardV2Calculator,
)
from backend.common.helpers.insights_v2.names import InsightV2NameEntry, InsightV2Names
from backend.common.models.event import Event
from backend.common.models.insight_v2 import LeaderboardKeyType, LeaderboardRankingV2


class BlueBannersV2Calculator(LeaderboardV2Calculator):
    @property
    def insight_name(self) -> InsightV2NameEntry:
        return InsightV2Names.BLUE_BANNERS

    @property
    def key_type(self) -> LeaderboardKeyType:
        return "team"

    def _build_rankings(self, counts: Dict[str, int]) -> List[LeaderboardRankingV2]:
        return build_leaderboard_rankings(counts)

    def on_event(self, event: Event) -> None:
        for award in event.awards:
            if award.award_type_enum in BLUE_BANNER_AWARDS and award.count_banner:
                for team_key in award.team_list:
                    self._increment(str(team_key.id()))
