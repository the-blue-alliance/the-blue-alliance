from backend.common.consts.alliance_color import AllianceColor
from backend.common.helpers.insights_v2.leaderboards.calculator import (
    MatchAllianceLeaderboardV2Calculator,
)
from backend.common.helpers.insights_v2.match_alliance_points import (
    get_total_points,
    MatchAlliancePoints,
)
from backend.common.helpers.insights_v2.names import InsightV2NameEntry, InsightV2Names
from backend.common.models.event import Event


class HighestLosingScoreV2Calculator(MatchAllianceLeaderboardV2Calculator):
    @property
    def insight_name(self) -> InsightV2NameEntry:
        return InsightV2Names.HIGHEST_LOSING_SCORE

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

            red_total = get_total_points(red_pts)
            blue_total = get_total_points(blue_pts)

            if red_total == blue_total:
                continue

            if red_total < blue_total:
                losing_score = red_total
                losing_color = AllianceColor.RED
            else:
                losing_score = blue_total
                losing_color = AllianceColor.BLUE

            if losing_score < 0:
                continue

            self._record_match(
                match_key=match.key_name,  # type: ignore[union-attr]
                score=losing_score,
                alliance=list(match.alliances[losing_color]["teams"]),  # type: ignore[index]
            )
