from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from pyre_extensions import none_throws

from backend.common.consts.alliance_color import AllianceColor
from backend.common.consts.comp_level import CompLevel
from backend.common.frc_api.types import ScoreDetailModelAlliance2026
from backend.common.game_specific.base import (
    PredictionStatConfig,
    StatAccessor,
    TCriteria,
    TripleWinTotalPointsScoreBonusRpGameConfig,
)
from backend.common.models.event_insights import EventInsights
from backend.common.models.match import Match
from backend.common.models.ranking_sort_order_info import RankingSortOrderInfo


class GameSpecifics2026(
    TripleWinTotalPointsScoreBonusRpGameConfig[ScoreDetailModelAlliance2026]
):
    SCORE_BREAKDOWN_MODEL = ScoreDetailModelAlliance2026
    BONUS_RP_BREAKDOWN_FIELDS = (
        "energizedAchieved",
        "superchargedAchieved",
        "traversalAchieved",
    )
    BONUS_RP_PREDICTION_FIELDS = (
        "prob_energized_bonus",
        "prob_supercharged_bonus",
        "prob_traversal_bonus",
    )

    def tiebreak_criteria(
        self, red: ScoreDetailModelAlliance2026, blue: ScoreDetailModelAlliance2026
    ) -> List[TCriteria]:
        tiebreakers: List[TCriteria] = []

        # Cumulative MAJOR FOUL points due to opponent rule violations
        if "majorFoulCount" in red and "majorFoulCount" in blue:
            tiebreakers.append((blue["majorFoulCount"], red["majorFoulCount"]))
        else:
            tiebreakers.append(None)

        # ALLIANCE AUTO FUEL points (hub / processor scoring in AUTO)
        red_hub = red.get("hubScore")
        blue_hub = blue.get("hubScore")
        if (
            isinstance(red_hub, dict)
            and isinstance(blue_hub, dict)
            and "autoPoints" in red_hub
            and "autoPoints" in blue_hub
        ):
            tiebreakers.append((red_hub["autoPoints"], blue_hub["autoPoints"]))
        else:
            tiebreakers.append(None)

        # ALLIANCE TOWER points
        if "totalTowerPoints" in red and "totalTowerPoints" in blue:
            tiebreakers.append((red["totalTowerPoints"], blue["totalTowerPoints"]))
        else:
            tiebreakers.append(None)

        return tiebreakers

    def calculate_event_insights(self, matches: List[Match]) -> Optional[EventInsights]:
        qual_matches = []
        playoff_matches = []
        for match in matches:
            if match.comp_level == CompLevel.QM:
                qual_matches.append(match)
            else:
                playoff_matches.append(match)

        qual_insights = self._calculate_event_insights_2026_helper(qual_matches)
        playoff_insights = self._calculate_event_insights_2026_helper(playoff_matches)

        return {
            "qual": qual_insights,
            "playoff": playoff_insights,
        }

    def _calculate_event_insights_2026_helper(
        self, matches: List[Match]
    ) -> Optional[Dict[str, Any]]:
        energized_rp_count = 0
        supercharged_rp_count = 0
        traversal_rp_count = 0
        six_rp_count = 0
        nine_rp_count = 0

        auto_win_conversion = 0
        undefined_auto_conversion_matches = 0

        auto_fuel_scored = 0
        teleop_fuel_scored = 0
        total_fuel_scored = 0

        auto_climb_count = 0
        endgame_climb_count = [0, 0, 0]

        total_scores = 0
        total_win_margins = 0
        total_winning_scores = 0

        high_score: Tuple[int, str, str] = (0, "", "")

        finished_matches = 0

        def determine_auto_winner(red, blue) -> Optional[AllianceColor]:
            # Compare total auto points
            if red.get("totalAutoPoints") > blue.get("totalAutoPoints"):
                return AllianceColor.RED
            if blue.get("totalAutoPoints") > red.get("totalAutoPoints"):
                return AllianceColor.BLUE

            # Auto tied: compare shift 1
            if red.get("hubScore").get("shift1Count") > 0:
                return AllianceColor.BLUE
            if blue.get("hubScore").get("shift1Count") > 0:
                return AllianceColor.RED

            # No scoring in shift 1: compare shift 2
            if red.get("hubScore").get("shift2Count") > 0:
                return AllianceColor.RED
            if blue.get("hubScore").get("shift2Count") > 0:
                return AllianceColor.BLUE

            # No scoring in shift 2: compare shift 3
            if red.get("hubScore").get("shift3Count") > 0:
                return AllianceColor.BLUE
            if blue.get("hubScore").get("shift3Count") > 0:
                return AllianceColor.RED

            # No scoring in shift 3: compare shift 4
            if red.get("hubScore").get("shift4Count") > 0:
                return AllianceColor.RED
            if blue.get("hubScore").get("shift4Count") > 0:
                return AllianceColor.BLUE

            # Fully tied
            return None

        for match in matches:
            if not match.has_been_played:
                continue

            finished_matches += 1

            red_score = match.alliances[AllianceColor.RED]["score"]
            blue_score = match.alliances[AllianceColor.BLUE]["score"]
            win_score = max(red_score, blue_score)

            if win_score > high_score[0]:
                high_score = (win_score, match.key_name, match.short_name)

            if match.score_breakdown is None:
                continue

            red_sb = none_throws(match.score_breakdown)[AllianceColor.RED]
            blue_sb = none_throws(match.score_breakdown)[AllianceColor.BLUE]

            if red_sb.get("energizedAchieved"):
                energized_rp_count += 1
            if blue_sb.get("energizedAchieved"):
                energized_rp_count += 1

            if red_sb.get("superchargedAchieved"):
                supercharged_rp_count += 1
            if blue_sb.get("superchargedAchieved"):
                supercharged_rp_count += 1

            if red_sb.get("traversalAchieved"):
                traversal_rp_count += 1
            if blue_sb.get("traversalAchieved"):
                traversal_rp_count += 1

            red_all_rp = (
                red_sb.get("energizedAchieved")
                and red_sb.get("superchargedAchieved")
                and red_sb.get("traversalAchieved")
            )
            blue_all_rp = (
                blue_sb.get("energizedAchieved")
                and blue_sb.get("superchargedAchieved")
                and blue_sb.get("traversalAchieved")
            )

            if (red_score > blue_score and red_all_rp) or (
                blue_score > red_score and blue_all_rp
            ):
                six_rp_count += 1
                if red_all_rp and blue_all_rp:
                    nine_rp_count += 1

            auto_winner = determine_auto_winner(red_sb, blue_sb)

            if (auto_winner is None) or (red_score == blue_score):
                undefined_auto_conversion_matches += 1
            elif (auto_winner == AllianceColor.RED) and (red_score > blue_score):
                auto_win_conversion += 1
            elif (auto_winner == AllianceColor.BLUE) and (blue_score > red_score):
                auto_win_conversion += 1

            for i in range(3):
                if red_sb.get("autoTowerRobot{}".format(i + 1)) != "None":
                    auto_climb_count += 1
                if blue_sb.get("autoTowerRobot{}".format(i + 1)) != "None":
                    auto_climb_count += 1

            auto_fuel_scored += red_sb.get("hubScore").get("autoCount")
            auto_fuel_scored += blue_sb.get("hubScore").get("autoCount")

            teleop_fuel_scored += red_sb.get("hubScore").get("teleopCount")
            teleop_fuel_scored += blue_sb.get("hubScore").get("teleopCount")

            total_fuel_scored = auto_fuel_scored + teleop_fuel_scored

            for i in range(3):
                tower_level = red_sb.get("endGameTowerRobot{}".format(i + 1))
                if tower_level == "Level1":
                    endgame_climb_count[0] += 1
                if tower_level == "Level2":
                    endgame_climb_count[1] += 1
                if tower_level == "Level3":
                    endgame_climb_count[2] += 1

            for i in range(3):
                tower_level = blue_sb.get("endGameTowerRobot{}".format(i + 1))
                if tower_level == "Level1":
                    endgame_climb_count[0] += 1
                if tower_level == "Level2":
                    endgame_climb_count[1] += 1
                if tower_level == "Level3":
                    endgame_climb_count[2] += 1

            total_scores += red_score + blue_score
            total_win_margins += win_score - min(red_score, blue_score)
            total_winning_scores += win_score

        if finished_matches == 0:
            return None

        return {
            "energized_rp_count": [
                energized_rp_count,
                finished_matches * 2,
                100.0 * energized_rp_count / (finished_matches * 2),
            ],
            "supercharged_rp_count": [
                supercharged_rp_count,
                finished_matches * 2,
                100.0 * supercharged_rp_count / (finished_matches * 2),
            ],
            "traversal_rp_count": [
                traversal_rp_count,
                finished_matches * 2,
                100.0 * traversal_rp_count / (finished_matches * 2),
            ],
            "six_rp_count": [
                six_rp_count,
                finished_matches,
                100.0 * six_rp_count / finished_matches,
            ],
            "nine_rp_count": [
                nine_rp_count,
                finished_matches,
                100.0 * nine_rp_count / finished_matches,
            ],
            "auto_win_conversion": [
                auto_win_conversion,
                finished_matches - undefined_auto_conversion_matches,
                (
                    0
                    if (finished_matches - undefined_auto_conversion_matches) == 0
                    else 100.0
                    * auto_win_conversion
                    / (finished_matches - undefined_auto_conversion_matches)
                ),
            ],
            "auto_fuel_scored": [
                auto_fuel_scored,
                auto_fuel_scored / (finished_matches * 2),
                auto_fuel_scored / (finished_matches * 6),
            ],
            "teleop_fuel_scored": [
                teleop_fuel_scored,
                teleop_fuel_scored / (finished_matches * 2),
                teleop_fuel_scored / (finished_matches * 6),
            ],
            "total_fuel_scored": [
                total_fuel_scored,
                total_fuel_scored / (finished_matches * 2),
                total_fuel_scored / (finished_matches * 6),
            ],
            "auto_climb_count": [
                auto_climb_count,
                finished_matches * 4,
                100.0 * auto_climb_count / (finished_matches * 4),
            ],
            "level1_climb_count": [
                endgame_climb_count[0],
                finished_matches * 6,
                100.0 * endgame_climb_count[0] / (finished_matches * 6),
            ],
            "level2_climb_count": [
                endgame_climb_count[1],
                finished_matches * 6,
                100.0 * endgame_climb_count[1] / (finished_matches * 6),
            ],
            "level3_climb_count": [
                endgame_climb_count[2],
                finished_matches * 6,
                100.0 * endgame_climb_count[2] / (finished_matches * 6),
            ],
            "average_score": total_scores / (finished_matches * 2),
            "average_win_margin": total_win_margins / finished_matches,
            "average_winning_score": total_winning_scores / finished_matches,
            "high_score": high_score,
        }

    def get_manual_coprs(self) -> Dict[str, StatAccessor]:
        return {
            "Hub Auto Fuel Count": lambda match, color: match.score_breakdown[color][
                "hubScore"
            ].get("autoCount", 0),
            "Hub Teleop Fuel Count": lambda match, color: match.score_breakdown[color][
                "hubScore"
            ].get("teleopCount", 0),
            "Hub Endgame Fuel Count": lambda match, color: match.score_breakdown[color][
                "hubScore"
            ].get("endgameCount", 0),
            "Hub Total Fuel Count": lambda match, color: match.score_breakdown[color][
                "hubScore"
            ].get("totalCount", 0),
            "Hub Transition Fuel Count": lambda match, color: match.score_breakdown[
                color
            ]["hubScore"].get("transitionCount", 0),
            "Hub Shift 1 Fuel Count": lambda match, color: match.score_breakdown[color][
                "hubScore"
            ].get("shift1Count", 0),
            "Hub Shift 2 Fuel Count": lambda match, color: match.score_breakdown[color][
                "hubScore"
            ].get("shift2Count", 0),
            "Hub Shift 3 Fuel Count": lambda match, color: match.score_breakdown[color][
                "hubScore"
            ].get("shift3Count", 0),
            "Hub Shift 4 Fuel Count": lambda match, color: match.score_breakdown[color][
                "hubScore"
            ].get("shift4Count", 0),
            "Hub First Active Shift Count": lambda match, color: (
                match.score_breakdown[color]["hubScore"].get("shift1Count", 0)
                + match.score_breakdown[color]["hubScore"].get("shift2Count", 0)
            ),
            "Hub Second Active Shift Count": lambda match, color: (
                match.score_breakdown[color]["hubScore"].get("shift3Count", 0)
                + match.score_breakdown[color]["hubScore"].get("shift4Count", 0)
            ),
            "Hub Uncounted": lambda match, color: match.score_breakdown[color][
                "hubScore"
            ].get("uncounted", 0),
        }

    def get_prediction_relevant_stats(self) -> List[PredictionStatConfig]:
        return [
            PredictionStatConfig("score", 0, 20**2),
            PredictionStatConfig("totalAutoPoints", 0, 10**2),
            PredictionStatConfig("totalTeleopPoints", 0, 10**2),
            PredictionStatConfig("endGameTowerPoints", 0, 10**2),
        ]

    def ranking_sort_order_info(self) -> Optional[List[RankingSortOrderInfo]]:
        return [
            {"name": "Ranking Score", "precision": 2},
            {"name": "Avg Match", "precision": 2},
            {"name": "Avg Auto Fuel", "precision": 2},
            {"name": "Avg Tower", "precision": 2},
        ]
