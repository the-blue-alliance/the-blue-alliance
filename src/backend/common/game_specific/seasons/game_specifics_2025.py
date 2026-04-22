from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple, TypedDict

from pyre_extensions import none_throws

from backend.common.consts.alliance_color import AllianceColor
from backend.common.consts.comp_level import CompLevel
from backend.common.frc_api.types import ScoreDetailModelAlliance2025
from backend.common.game_specific.base import (
    PredictionStatConfig,
    StatAccessor,
    TCriteria,
    TripleWinTotalPointsScoreBonusRpGameConfig,
)
from backend.common.models.event_insights import EventInsights
from backend.common.models.match import Match
from backend.common.models.ranking_sort_order_info import RankingSortOrderInfo


class GameSpecifics2025(
    TripleWinTotalPointsScoreBonusRpGameConfig[ScoreDetailModelAlliance2025]
):
    SCORE_BREAKDOWN_MODEL = ScoreDetailModelAlliance2025
    BONUS_RP_BREAKDOWN_FIELDS = (
        "autoBonusAchieved",
        "coralBonusAchieved",
        "bargeBonusAchieved",
    )
    BONUS_RP_PREDICTION_FIELDS = (
        "prob_auto_coral_bonus",
        "prob_coral_bonus",
        "prob_barge_bonus",
    )

    def tiebreak_criteria(
        self, red: ScoreDetailModelAlliance2025, blue: ScoreDetailModelAlliance2025
    ) -> List[TCriteria]:
        tiebreakers: List[TCriteria] = []

        # TECH FOUL points due to opponent rule violations
        # Since tech foul points are not provided, we use the count instead.
        if "techFoulCount" in red and "techFoulCount" in blue:
            tiebreakers.append((blue["techFoulCount"], red["techFoulCount"]))
        else:
            tiebreakers.append(None)

        # ALLIANCE AUTO points
        if "autoPoints" in red and "autoPoints" in blue:
            tiebreakers.append(
                (
                    red["autoPoints"],
                    blue["autoPoints"],
                )
            )
        else:
            tiebreakers.append(None)

        # ALLIANCE BARGE points
        if "endGameBargePoints" in red and "endGameBargePoints" in blue:
            tiebreakers.append(
                (
                    red["endGameBargePoints"],
                    blue["endGameBargePoints"],
                )
            )
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

        qual_insights = self._calculate_event_insights_2025_helper(qual_matches)
        playoff_insights = self._calculate_event_insights_2025_helper(playoff_matches)

        return {
            "qual": qual_insights,
            "playoff": playoff_insights,
        }

    def _calculate_event_insights_2025_helper(
        self, matches: List[Match]
    ) -> Optional[Dict[str, Any]]:
        auto_rp_count = 0
        barge_rp_count = 0
        coral_rp_count = 0
        coopertition_count = 0
        six_rp_count = 0
        nine_rp_count = 0

        total_scores = 0
        total_win_margins = 0
        total_winning_scores = 0

        high_score: Tuple[int, str, str] = (0, "", "")

        finished_matches = 0

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

            if red_sb.get("autoBonusAchieved"):
                auto_rp_count += 1
            if blue_sb.get("autoBonusAchieved"):
                auto_rp_count += 1

            if red_sb.get("bargeBonusAchieved"):
                barge_rp_count += 1
            if blue_sb.get("bargeBonusAchieved"):
                barge_rp_count += 1

            if red_sb.get("coralBonusAchieved"):
                coral_rp_count += 1
            if blue_sb.get("coralBonusAchieved"):
                coral_rp_count += 1

            if red_sb.get("coopertitionCriteriaMet"):
                coopertition_count += 1
            if blue_sb.get("coopertitionCriteriaMet"):
                coopertition_count += 1

            red_all_rp = (
                red_sb.get("autoBonusAchieved")
                and red_sb.get("bargeBonusAchieved")
                and red_sb.get("coralBonusAchieved")
            )
            blue_all_rp = (
                blue_sb.get("autoBonusAchieved")
                and blue_sb.get("bargeBonusAchieved")
                and blue_sb.get("coralBonusAchieved")
            )

            if (red_score > blue_score and red_all_rp) or (
                blue_score > red_score and blue_all_rp
            ):
                six_rp_count += 1
                if red_all_rp and blue_all_rp:
                    nine_rp_count += 1

            total_scores += red_score + blue_score
            total_win_margins += win_score - min(red_score, blue_score)
            total_winning_scores += win_score

        if finished_matches == 0:
            return None

        return {
            "auto_rp_count": [
                auto_rp_count,
                finished_matches * 2,
                100.0 * auto_rp_count / (finished_matches * 2),
            ],
            "barge_rp_count": [
                barge_rp_count,
                finished_matches * 2,
                100.0 * barge_rp_count / (finished_matches * 2),
            ],
            "coral_rp_count": [
                coral_rp_count,
                finished_matches * 2,
                100.0 * coral_rp_count / (finished_matches * 2),
            ],
            "coopertition_count": [
                coopertition_count,
                finished_matches * 2,
                100.0 * coopertition_count / (finished_matches * 2),
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
            "average_score": total_scores / (finished_matches * 2),
            "average_win_margin": total_win_margins / finished_matches,
            "average_winning_score": total_winning_scores / finished_matches,
            "high_score": high_score,
        }

    def get_manual_coprs(self) -> Dict[str, StatAccessor]:
        return {
            "L1 Coral Count": lambda match, color: (
                match.score_breakdown[color].get("autoReef", {}).get("trough", 0)
                + match.score_breakdown[color].get("teleopReef", {}).get("trough", 0)
            ),
            "L2 Coral Count": lambda match, color: (
                match.score_breakdown[color]
                .get("teleopReef", {})
                .get("tba_botRowCount", 0)
            ),
            "L3 Coral Count": lambda match, color: (
                match.score_breakdown[color]
                .get("teleopReef", {})
                .get("tba_midRowCount", 0)
            ),
            "L4 Coral Count": lambda match, color: (
                match.score_breakdown[color]
                .get("teleopReef", {})
                .get("tba_topRowCount", 0)
            ),
            "Total Coral Count": lambda match, color: sum(
                [
                    match.score_breakdown[color].get("autoCoralCount", 0),
                    match.score_breakdown[color].get("teleopCoralCount", 0),
                ]
            ),
            "Total Coral Points": lambda match, color: sum(
                [
                    match.score_breakdown[color].get("autoCoralPoints", 0),
                    match.score_breakdown[color].get("teleopCoralPoints", 0),
                ]
            ),
            "Total Algae Count": lambda match, color: sum(
                [
                    match.score_breakdown[color].get("wallAlgaeCount", 0),
                    match.score_breakdown[color].get("netAlgaeCount", 0),
                ]
            ),
            "Total Game Piece Count": lambda match, color: sum(
                [
                    match.score_breakdown[color].get("autoCoralCount", 0),
                    match.score_breakdown[color].get("teleopCoralCount", 0),
                    match.score_breakdown[color].get("wallAlgaeCount", 0),
                    match.score_breakdown[color].get("netAlgaeCount", 0),
                ]
            ),
        }

    def get_prediction_relevant_stats(self) -> List[PredictionStatConfig]:
        return [
            PredictionStatConfig("score", 0, 20**2),
            PredictionStatConfig("auto_coral_scored", 0, 2**2),
            PredictionStatConfig("coral_scored", 0, 10**2),
            PredictionStatConfig("barge_points", 0, 10**2),
        ]

    def ranking_sort_order_info(self) -> Optional[List[RankingSortOrderInfo]]:
        return [
            {"name": "Ranking Score", "precision": 2},
            {"name": "Avg Coop", "precision": 2},
            {"name": "Avg Match", "precision": 2},
            {"name": "Avg Auto", "precision": 2},
            {"name": "Avg Barge", "precision": 2},
        ]


class _RankingBreakdown2025(TypedDict):
    autoBonusAchieved: bool
    coralBonusAchieved: bool
    bargeBonusAchieved: bool


class _RankingPrediction2025(TypedDict):
    prob_auto_coral_bonus: float
    prob_coral_bonus: float
    prob_barge_bonus: float
