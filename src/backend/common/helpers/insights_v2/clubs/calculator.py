from abc import abstractmethod
from typing import Dict, List, Optional

from backend.common.helpers.insights_v2.base import InsightV2Calculator
from backend.common.helpers.insights_v2.names import InsightV2NameEntry
from backend.common.models.insight_v2 import (
    ClubContextType,
    ClubEntry,
    ClubEntryV2,
    ClubEntryWithHallOfFame,
    ClubsData,
    HallOfFameClubContext,
    InsightCategory,
    InsightV2,
)
from backend.common.models.keys import Year


class ClubV2Calculator(InsightV2Calculator):
    """
    Base class for club insights. A club is a cumulative, all-time membership of
    teams that reached a milestone. Each member has an event_added_key (where they
    first qualified) and an optional club-specific extra_context. All-time only
    (year=0), global (no district scoping).
    """

    def __init__(self) -> None:
        self._first_event: Dict[str, str] = {}

    @property
    @abstractmethod
    def insight_name(self) -> InsightV2NameEntry: ...

    @property
    @abstractmethod
    def context_type(self) -> ClubContextType: ...

    def _record(self, team_key: str, event_key: str) -> None:
        self._first_event.setdefault(team_key, event_key)

    def _extra_context_for(
        self, team_key: str, event_added_key: str
    ) -> Optional[HallOfFameClubContext]:
        return None

    def make_insights(
        self, year: Year, team_to_district: Dict[str, str]
    ) -> List[InsightV2]:
        if year != 0 or not self._first_event:
            return []

        entries: List[ClubEntry] = []
        for team_key in sorted(self._first_event, key=lambda k: int(k[3:])):
            event_added_key = self._first_event[team_key]
            extra_context = self._extra_context_for(team_key, event_added_key)
            if extra_context is None:
                entries.append(
                    ClubEntryV2(team_key=team_key, event_added_key=event_added_key)
                )
            else:
                entries.append(
                    ClubEntryWithHallOfFame(
                        team_key=team_key,
                        event_added_key=event_added_key,
                        extra_context=extra_context,
                    )
                )

        data = ClubsData(entries=entries, context_type=self.context_type)
        return [
            InsightV2(
                id=InsightV2.render_key_name(
                    0, InsightCategory.CLUBS, self.insight_name.name
                ),
                name=self.insight_name.name,
                display_name=self.insight_name.display_name,
                year=0,
                category=InsightCategory.CLUBS,
                data_json=data,
            )
        ]
