from typing import Set

from backend.common.consts.award_type import AwardType
from backend.common.consts.event_type import EventType
from backend.common.helpers.insights_v2.streak_calculator import StreakV2Calculator
from backend.common.models.event import Event
from backend.common.models.insight_v2 import InsightV2NameEntry, InsightV2Names

_QUALIFYING_EVENT_TYPES = {EventType.REGIONAL, EventType.DISTRICT}


class LongestQualifyingEventStreakV2Calculator(StreakV2Calculator):
    @property
    def insight_name(self) -> InsightV2NameEntry:
        return InsightV2Names.QUALIFYING_EVENT_WIN_STREAK

    def on_event(self, event: Event) -> None:
        if event.event_type_enum not in _QUALIFYING_EVENT_TYPES:
            return
        # Skip cancelled events with no matches (e.g. 2020 season)
        if not event.matches:
            return

        label = event.key_name

        winners: Set[str] = set()
        for award in event.awards:
            if award.award_type_enum == AwardType.WINNER:
                for team_key in award.team_list:
                    key = str(team_key.id())
                    self._advance_streak(key, label)
                    winners.add(key)

        for match in event.matches:
            for team_key in match.team_key_names:
                if team_key not in winners:
                    self._reset_streak(team_key)
