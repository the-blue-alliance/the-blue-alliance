from backend.common.consts.alliance_color import AllianceColor
from backend.common.helpers.insights_v2.leaderboards.calculator import (
    MatchAllianceLeaderboardV2Calculator,
)
from backend.common.helpers.insights_v2.match_alliance_points import (
    get_teleop_points,
    MatchAlliancePoints,
)
from backend.common.helpers.insights_v2.names import InsightV2NameEntry, InsightV2Names
from backend.common.models.event import Event


class HighestTeleopScoreV2Calculator(MatchAllianceLeaderboardV2Calculator):
    @property
    def insight_name(self) -> InsightV2NameEntry:
        return InsightV2Names.HIGHEST_TELEOP_SCORE

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

            red_teleop = get_teleop_points(red_pts)
            if red_teleop is None:
                continue

            blue_teleop = get_teleop_points(blue_pts)
            if blue_teleop is None:
                continue

            if red_teleop >= blue_teleop:
                high_score = red_teleop
                high_color = AllianceColor.RED
            else:
                high_score = blue_teleop
                high_color = AllianceColor.BLUE

            self._record_match(
                match_key=match.key_name,  # type: ignore[union-attr]
                score=high_score,
                alliance=list(match.alliances[high_color]["teams"]),  # type: ignore[index]
            )
