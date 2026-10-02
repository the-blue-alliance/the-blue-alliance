from abc import abstractmethod
from typing import Dict, Optional

from backend.common.consts.alliance_color import AllianceColor
from backend.common.helpers.insights_v2.leaderboards.calculator import (
    MatchAllianceLeaderboardV2Calculator,
)
from backend.common.helpers.insights_v2.match_alliance_points import (
    get_game_piece_count,
    MatchAlliancePoints,
)
from backend.common.helpers.insights_v2.names import InsightV2NameEntry, InsightV2Names
from backend.common.models.event import Event
from backend.common.models.keys import Year

# Per-year game-specific label for what this insight measures. Falls back to
# insight_name.display_name ("Most Game Pieces Scored") for any year not listed
# here.
_DISPLAY_NAMES: Dict[int, str] = {
    2016: "Most Boulders Scored",
    2017: "Most Fuel Scored",
    2020: "Most Power Cells Scored",
    2022: "Most Cargo Scored",
    2024: "Most Notes Scored",
    2025: "Most Coral Scored",
    2026: "Most Fuel Scored",
}


class HighestCountByMatchV2Calculator(MatchAllianceLeaderboardV2Calculator):
    """
    Base class for match-level leaderboards that record the higher of the two
    alliances' scores for some year-specific count (e.g. game pieces scored).
    Subclasses implement `_count`; matches/years the count doesn't apply to are
    skipped by returning None.
    """

    @abstractmethod
    def _count(self, match_alliance: MatchAlliancePoints) -> Optional[int]: ...

    def on_event(self, event: Event) -> None:
        for match in event.matches or []:
            if not match.has_been_played:
                continue

            red_pts = MatchAlliancePoints(
                score=int(match.alliances[AllianceColor.RED]["score"]),  # type: ignore[index]
                breakdown=(
                    match.score_breakdown[AllianceColor.RED]
                    if match.score_breakdown
                    else None
                ),
                year=match.year,
            )
            blue_pts = MatchAlliancePoints(
                score=int(match.alliances[AllianceColor.BLUE]["score"]),  # type: ignore[index]
                breakdown=(
                    match.score_breakdown[AllianceColor.BLUE]
                    if match.score_breakdown
                    else None
                ),
                year=match.year,
            )

            red_count = self._count(red_pts)
            if red_count is None:
                continue

            blue_count = self._count(blue_pts)
            if blue_count is None:
                continue

            if red_count >= blue_count:
                high_count = red_count
                high_color = AllianceColor.RED
            else:
                high_count = blue_count
                high_color = AllianceColor.BLUE

            self._record_match(
                match_key=match.key_name,  # type: ignore[union-attr]
                score=high_count,
                alliance=list(match.alliances[high_color]["teams"]),  # type: ignore[index]
            )


class MostGamePiecesScoredV2Calculator(HighestCountByMatchV2Calculator):
    @property
    def insight_name(self) -> InsightV2NameEntry:
        return InsightV2Names.MOST_GAME_PIECES_SCORED

    def display_name_for(self, year: Year) -> str:
        return _DISPLAY_NAMES.get(year, self.insight_name.display_name)

    def _count(self, match_alliance: MatchAlliancePoints) -> Optional[int]:
        return get_game_piece_count(match_alliance)
