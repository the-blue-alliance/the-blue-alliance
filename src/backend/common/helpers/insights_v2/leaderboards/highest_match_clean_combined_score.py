from backend.common.consts.alliance_color import AllianceColor
from backend.common.helpers.insights_v2.leaderboards.calculator import (
    MatchAllianceLeaderboardV2Calculator,
)
from backend.common.helpers.insights_v2.match_alliance_points import (
    get_foul_points,
    get_total_points,
    MatchAlliancePoints,
)
from backend.common.helpers.insights_v2.names import InsightV2NameEntry, InsightV2Names
from backend.common.models.event import Event


class HighestMatchCleanCombinedScoreV2Calculator(MatchAllianceLeaderboardV2Calculator):
    @property
    def insight_name(self) -> InsightV2NameEntry:
        return InsightV2Names.HIGHEST_MATCH_CLEAN_COMBINED_SCORE

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

            red_clean = get_total_points(red_pts) - get_foul_points(red_pts)
            blue_clean = get_total_points(blue_pts) - get_foul_points(blue_pts)

            if red_clean < 0 or blue_clean < 0:
                continue

            combined = red_clean + blue_clean
            all_teams = list(match.alliances[AllianceColor.RED]["teams"]) + list(  # type: ignore[index]
                match.alliances[AllianceColor.BLUE]["teams"]  # type: ignore[index]
            )

            self._record_match(
                match_key=match.key_name,  # type: ignore[union-attr]
                score=combined,
                alliance=all_teams,
            )
