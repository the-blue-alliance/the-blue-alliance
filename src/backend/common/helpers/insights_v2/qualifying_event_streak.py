from typing import Dict, List, Set

from backend.common.consts.award_type import AwardType
from backend.common.consts.event_type import EventType
from backend.common.helpers.insights_v2.streak_calculator import StreakV2Calculator
from backend.common.models.event import Event
from backend.common.models.insight_v2 import (
    InsightCategory,
    InsightV2,
    InsightV2NameEntry,
    InsightV2Names,
    StreakData,
)
from backend.common.models.keys import Year

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

    def make_insights(
        self, year: Year, team_to_district: Dict[str, str]
    ) -> List[InsightV2]:
        # Build the full sorted list once; use it for both global and district scopes
        all_entries = self._build_streak_entries()
        if not all_entries:
            return []

        name = self.insight_name
        insights: List[InsightV2] = [
            InsightV2(
                id=InsightV2.render_key_name(year, InsightCategory.STREAK, name.name),
                name=name.name,
                display_name=name.display_name,
                year=year,
                category=InsightCategory.STREAK,
                data_json=StreakData(entries=all_entries),
            )
        ]

        for district_abbrev, d_entries in sorted(
            self._build_district_entries(all_entries, team_to_district).items()
        ):
            insights.append(
                InsightV2(
                    id=InsightV2.render_key_name(
                        year, InsightCategory.STREAK, name.name, district_abbrev
                    ),
                    name=name.name,
                    display_name=name.display_name,
                    year=year,
                    category=InsightCategory.STREAK,
                    district_abbreviation=district_abbrev,
                    data_json=StreakData(entries=d_entries),
                )
            )

        return insights
