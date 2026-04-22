from collections import defaultdict
from typing import Dict, Optional

from backend.common.consts.award_type import BLUE_BANNER_AWARDS
from backend.common.helpers.insights_v2.compute import (
    build_leaderboard_rankings,
    InsightV2Calculator,
)
from backend.common.models.event import Event
from backend.common.models.insight_v2 import (
    InsightCategory,
    InsightV2,
    InsightV2Name,
    LeaderboardDataV2,
)
from backend.common.models.keys import Year

BLUE_BANNERS_DISPLAY_NAME = "Total Blue Banners"


class BlueBannersV2Calculator(InsightV2Calculator):
    def __init__(self) -> None:
        self.counts: Dict[str, int] = defaultdict(int)

    def on_event(self, event: Event) -> None:
        for award in event.awards:
            if award.award_type_enum in BLUE_BANNER_AWARDS and award.count_banner:
                for team_key in award.team_list:
                    self.counts[str(team_key.id())] += 1

    def make_insight(self, year: Year) -> Optional[InsightV2]:
        if not self.counts:
            return None

        data = LeaderboardDataV2(
            rankings=build_leaderboard_rankings(self.counts),
            key_type="team",
        )
        return InsightV2(
            id=InsightV2.render_key_name(
                year, InsightCategory.LEADERBOARD, InsightV2Name.BLUE_BANNERS
            ),
            name=InsightV2Name.BLUE_BANNERS,
            display_name=BLUE_BANNERS_DISPLAY_NAME,
            year=year,
            category=InsightCategory.LEADERBOARD,
            data_json=data,
        )
