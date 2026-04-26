from typing import Dict, List, Optional, Set

from backend.common.consts.award_type import AwardType
from backend.common.consts.event_type import EventType
from backend.common.helpers.insights_v2.streak_calculator import StreakV2Calculator
from backend.common.models.event import Event
from backend.common.models.insight_v2 import (
    InsightV2,
    InsightV2NameEntry,
    InsightV2Names,
)
from backend.common.models.keys import Year


class LongestEinsteinStreakV2Calculator(StreakV2Calculator):
    """
    Tracks consecutive years in which a team won the WINNER award at a
    CMP_DIVISION event. The streak resets in any year that has CMP_DIVISION
    events but the team did not win one. Years with no CMP_DIVISION events
    (e.g. 2020/2021 COVID cancellations) are skipped without resetting streaks.
    """

    def __init__(self) -> None:
        super().__init__()
        self._current_year: Optional[int] = None
        self._year_winners: Set[str] = set()
        self._had_cmp_divisions: bool = False

    @property
    def insight_name(self) -> InsightV2NameEntry:
        return InsightV2Names.EINSTEIN_WIN_STREAK

    def on_event(self, event: Event) -> None:
        year = event.year
        if self._current_year is not None and year != self._current_year:
            self._finalize_year(self._current_year)
        self._current_year = year

        if event.event_type_enum != EventType.CMP_DIVISION:
            return
        if not event.matches:  # Skip cancelled events
            return

        self._had_cmp_divisions = True
        for award in event.awards:
            if award.award_type_enum == AwardType.WINNER:
                for team_key in award.team_list:
                    self._year_winners.add(str(team_key.id()))

    def _finalize_year(self, year: int) -> None:
        if not self._had_cmp_divisions:
            # No CMP_DIVISION events this year — skip without resetting streaks.
            self._year_winners = set()
            return

        label = str(year)
        for key in self._year_winners:
            self._advance_streak(key, label)

        # Reset any team with an active streak that did not win a division this year.
        for key in list(self._active.keys()):
            if key not in self._year_winners:
                self._reset_streak(key)

        self._year_winners = set()
        self._had_cmp_divisions = False

    def make_insights(
        self, year: Year, team_to_district: Dict[str, str]
    ) -> List[InsightV2]:
        if self._current_year is not None:
            self._finalize_year(self._current_year)
            self._current_year = None
        return super().make_insights(year, team_to_district)
