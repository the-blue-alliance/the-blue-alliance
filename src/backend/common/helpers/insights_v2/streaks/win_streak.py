from backend.common.consts.alliance_color import ALLIANCE_COLORS
from backend.common.consts.comp_level import COMP_LEVELS_PLAY_ORDER
from backend.common.helpers.insights_v2.names import InsightV2NameEntry, InsightV2Names
from backend.common.helpers.insights_v2.streaks.calculator import StreakV2Calculator
from backend.common.models.event import Event


class LongestWinStreakV2Calculator(StreakV2Calculator):
    """
    Tracks the longest continuous run of match wins across a team's entire career.
    The streak crosses year boundaries. Ties are neutral: they neither advance
    nor break the streak.
    """

    @property
    def insight_name(self) -> InsightV2NameEntry:
        return InsightV2Names.WIN_STREAK

    def on_event(self, event: Event) -> None:
        if not event.matches:
            return

        label = event.key_name
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
                    if winning_alliance == color:
                        self._advance_streak(team_key, label)
                    elif winning_alliance != "":
                        self._reset_streak(team_key)
                    # Tie: no-op
