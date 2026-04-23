from backend.common.consts.award_type import BLUE_BANNER_AWARDS
from backend.common.helpers.insights_v2.compute import LeaderboardV2Calculator
from backend.common.models.event import Event
from backend.common.models.insight_v2 import (
    InsightV2NameEntry,
    InsightV2Names,
    LeaderboardKeyType,
)


class BlueBannersV2Calculator(LeaderboardV2Calculator):
    @property
    def insight_name(self) -> InsightV2NameEntry:
        return InsightV2Names.BLUE_BANNERS

    @property
    def key_type(self) -> LeaderboardKeyType:
        return "team"

    def on_event(self, event: Event) -> None:
        for award in event.awards:
            if award.award_type_enum in BLUE_BANNER_AWARDS and award.count_banner:
                for team_key in award.team_list:
                    self._increment(str(team_key.id()))
