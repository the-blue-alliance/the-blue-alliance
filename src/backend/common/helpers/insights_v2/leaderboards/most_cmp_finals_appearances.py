from backend.common.consts.award_type import AwardType
from backend.common.consts.event_type import EventType
from backend.common.helpers.insights_v2.leaderboards.calculator import (
    EventListLeaderboardV2Calculator,
)
from backend.common.helpers.insights_v2.names import InsightV2NameEntry, InsightV2Names
from backend.common.models.event import Event
from backend.common.models.insight_v2 import LeaderboardKeyType

_FINALS_AWARD_TYPES = {AwardType.WINNER, AwardType.FINALIST}


class MostCmpFinalsAppearancesV2Calculator(EventListLeaderboardV2Calculator):
    @property
    def insight_name(self) -> InsightV2NameEntry:
        return InsightV2Names.MOST_CMP_FINALS_APPEARANCES

    @property
    def key_type(self) -> LeaderboardKeyType:
        return "team"

    @property
    def min_count(self) -> int:
        return 1

    def on_event(self, event: Event) -> None:
        if event.event_type_enum != EventType.CMP_FINALS:
            return
        event_key = str(event.key.id())
        for award in event.awards:
            if award.award_type_enum in _FINALS_AWARD_TYPES:
                for team_key in award.team_list:
                    self._record_event(str(team_key.id()), event_key)
