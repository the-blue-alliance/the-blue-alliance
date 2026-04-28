from backend.common.consts.award_type import AwardType
from backend.common.helpers.insights_v2.leaderboards.calculator import (
    EventListLeaderboardV2Calculator,
)
from backend.common.helpers.insights_v2.names import InsightV2NameEntry, InsightV2Names
from backend.common.models.event import Event
from backend.common.models.insight_v2 import LeaderboardKeyType


class MostImpactAwardWinsV2Calculator(EventListLeaderboardV2Calculator):
    @property
    def insight_name(self) -> InsightV2NameEntry:
        return InsightV2Names.MOST_IMPACT_AWARD_WINS

    @property
    def key_type(self) -> LeaderboardKeyType:
        return "team"

    @property
    def min_count(self) -> int:
        return 2

    def on_event(self, event: Event) -> None:
        event_key = str(event.key.id())
        for award in event.awards:
            if award.award_type_enum == AwardType.CHAIRMANS:
                for team_key in award.team_list:
                    self._record_event(str(team_key.id()), event_key)
