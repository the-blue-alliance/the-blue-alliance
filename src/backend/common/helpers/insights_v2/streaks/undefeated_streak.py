from typing import Optional, Set

from backend.common.consts.alliance_color import ALLIANCE_COLORS
from backend.common.consts.comp_level import COMP_LEVELS_PLAY_ORDER
from backend.common.helpers.insights_v2.names import InsightV2NameEntry, InsightV2Names
from backend.common.helpers.insights_v2.streaks.calculator import StreakV2Calculator
from backend.common.models.event import Event


class LongestUndefeatedStreakV2Calculator(StreakV2Calculator):
    """
    Tracks the longest run of matches from the start of a season in which a team
    never lost. Ties count as non-losses. The streak resets each year; the first
    loss ends the season streak permanently regardless of subsequent wins.
    """

    def __init__(self) -> None:
        super().__init__()
        self._current_year: Optional[int] = None
        self._year_lost: Set[str] = set()

    @property
    def insight_name(self) -> InsightV2NameEntry:
        return InsightV2Names.UNDEFEATED_STREAK

    def on_event(self, event: Event) -> None:
        year = event.year
        if self._current_year is not None and year != self._current_year:
            self._finalize_year()
        self._current_year = year

        if not event.matches:
            return

        sorted_matches = sorted(
            event.matches,
            key=lambda m: (
                COMP_LEVELS_PLAY_ORDER.get(m.comp_level, 0),
                m.set_number,
                m.match_number,
            ),
        )

        for match in sorted_matches:
            if not match.has_been_played:
                continue

            winning_alliance = self._effective_winning_alliance(match)
            for color in ALLIANCE_COLORS:
                for team_key in match.alliances[color]["teams"]:
                    if team_key in self._year_lost:
                        continue
                    if winning_alliance == color or winning_alliance == "":
                        self._advance_streak(team_key, match.key_name)
                    else:
                        self._reset_streak(team_key)
                        self._year_lost.add(team_key)

    def _finalize_year(self) -> None:
        for key in list(self._active.keys()):
            self._reset_streak(key)
        self._year_lost.clear()
