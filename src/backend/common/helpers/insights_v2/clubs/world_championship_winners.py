from backend.common.consts.award_type import AwardType
from backend.common.consts.event_type import EventType
from backend.common.helpers.insights_v2.clubs.calculator import ClubV2Calculator
from backend.common.helpers.insights_v2.names import InsightV2NameEntry, InsightV2Names
from backend.common.models.event import Event
from backend.common.models.insight_v2 import ClubContextType


class WorldChampionshipWinnersClubV2Calculator(ClubV2Calculator):
    """
    Teams that have won a WINNER award at Championship finals
    (EventType.CMP_FINALS / Einstein). No extra_context.
    """

    @property
    def insight_name(self) -> InsightV2NameEntry:
        return InsightV2Names.WORLD_CHAMPIONSHIP_WINNERS

    @property
    def context_type(self) -> ClubContextType:
        return "none"

    def on_event(self, event: Event) -> None:
        if event.event_type_enum != EventType.CMP_FINALS:
            return
        event_key = str(event.key.id())
        for award in event.awards:
            if award.award_type_enum == AwardType.WINNER:
                for team_key in award.team_list:
                    self._record(str(team_key.id()), event_key)
