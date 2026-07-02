from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

from backend.common.consts.alliance_color import ALLIANCE_COLORS, AllianceColor
from backend.common.consts.comp_level import CompLevel
from backend.common.consts.event_type import SEASON_EVENT_TYPES
from backend.common.frc_api.types import ScoreDetailModelAlliance2016
from backend.common.game_specific.base import (
    BonusRpBreakdownSeasonGameConfig,
    PredictionStatConfig,
    TCriteria,
)
from backend.common.models.event_insights import EventInsights
from backend.common.models.match import Match
from backend.common.models.ranking_sort_order_info import RankingSortOrderInfo


class GameSpecifics2016(BonusRpBreakdownSeasonGameConfig[ScoreDetailModelAlliance2016]):
    SCORE_BREAKDOWN_MODEL = ScoreDetailModelAlliance2016
    BONUS_RP_BREAKDOWN_FIELDS = ("teleopDefensesBreached", "teleopTowerCaptured")
    BONUS_RP_PREDICTION_FIELDS = ("prob_breach", "prob_capture")

    def finals_can_be_tiebroken(self) -> bool:
        return True

    def tiebreak_criteria(
        self, red: ScoreDetailModelAlliance2016, blue: ScoreDetailModelAlliance2016
    ) -> List[TCriteria]:
        tiebreakers: List[TCriteria] = []

        # Greater number of FOUL points awarded (i.e. the ALLIANCE that played the cleaner MATCH)
        if "foulPoints" in red and "foulPoints" in blue:
            tiebreakers.append((red["foulPoints"], blue["foulPoints"]))
        else:
            tiebreakers.append(None)

        # Cumulative sum of BREACH and CAPTURE points
        if (
            "breachPoints" in red
            and "breachPoints" in blue
            and "capturePoints" in red
            and "capturePoints" in blue
        ):
            red_breach_capture = red["breachPoints"] + red["capturePoints"]
            blue_breach_capture = blue["breachPoints"] + blue["capturePoints"]
            tiebreakers.append((red_breach_capture, blue_breach_capture))
        else:
            tiebreakers.append(None)

        # Cumulative sum of scored AUTO points
        if "autoPoints" in red and "autoPoints" in blue:
            tiebreakers.append((red["autoPoints"], blue["autoPoints"]))
        else:
            tiebreakers.append(None)

        # Cumulative sum of scored SCALE and CHALLENGE points
        if (
            "teleopScalePoints" in red
            and "teleopScalePoints" in blue
            and "teleopChallengePoints" in red
            and "teleopChallengePoints" in blue
        ):
            red_scale_challenge = (
                red["teleopScalePoints"] + red["teleopChallengePoints"]
            )
            blue_scale_challenge = (
                blue["teleopScalePoints"] + blue["teleopChallengePoints"]
            )
            tiebreakers.append((red_scale_challenge, blue_scale_challenge))
        else:
            tiebreakers.append(None)

        # Cumulative sum of scored TOWER GOAL points (High and Low goals from AUTO and TELEOP)
        if (
            "autoBoulderPoints" in red
            and "autoBoulderPoints" in blue
            and "teleopBoulderPoints" in red
            and "teleopBoulderPoints" in blue
        ):
            red_boulder = red["autoBoulderPoints"] + red["teleopBoulderPoints"]
            blue_boulder = blue["autoBoulderPoints"] + blue["teleopBoulderPoints"]
            tiebreakers.append((red_boulder, blue_boulder))
        else:
            tiebreakers.append(None)

        # Cumulative sum of CROSSED UNDAMAGED DEFENSE points (AUTO and TELEOP)
        if (
            "autoCrossingPoints" in red
            and "autoCrossingPoints" in blue
            and "teleopCrossingPoints" in red
            and "teleopCrossingPoints" in blue
        ):
            red_crossing = red["autoCrossingPoints"] + red["teleopCrossingPoints"]
            blue_crossing = blue["autoCrossingPoints"] + blue["teleopCrossingPoints"]
            tiebreakers.append((red_crossing, blue_crossing))
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

        qual_insights = self._calculate_event_insights_2016_helper(qual_matches)
        playoff_insights = self._calculate_event_insights_2016_helper(playoff_matches)

        return {
            "qual": qual_insights,
            "playoff": playoff_insights,
        }

    def _calculate_event_insights_2016_helper(
        self, matches: List[Match]
    ) -> Optional[Dict[str, Any]]:
        # defenses
        defense_opportunities = defaultdict(int)
        defense_damaged = defaultdict(int)
        breaches = 0

        # towers
        high_goals = 0
        low_goals = 0
        challenges = 0
        scales = 0
        captures = 0

        # scores
        winning_scores = 0
        win_margins = 0
        total_scores = 0
        auto_scores = 0
        crossing_scores = 0
        boulder_scores = 0
        tower_scores = 0
        foul_scores = 0
        high_score: Tuple[int, str, str] = (0, "", "")  # score, match key, match name

        finished_matches = 0
        has_insights = False
        for match in matches:
            if not match.has_been_played:
                continue

            red_score = match.alliances[AllianceColor.RED]["score"]
            blue_score = match.alliances[AllianceColor.BLUE]["score"]
            win_score = max(red_score, blue_score)

            winning_scores += win_score
            win_margins += win_score - min(red_score, blue_score)
            total_scores += red_score + blue_score

            if win_score > high_score[0]:
                high_score = (win_score, match.key_name, match.short_name)

            score_breakdown = match.score_breakdown
            if not score_breakdown:
                continue

            for alliance_color in ALLIANCE_COLORS:
                try:
                    alliance_breakdown = score_breakdown[alliance_color]

                    auto_scores += alliance_breakdown["autoPoints"]
                    crossing_scores += alliance_breakdown["teleopCrossingPoints"]
                    boulder_scores += alliance_breakdown["teleopBoulderPoints"]
                    tower_scores += (
                        alliance_breakdown["teleopChallengePoints"]
                        + alliance_breakdown["teleopScalePoints"]
                    )
                    foul_scores += alliance_breakdown["foulPoints"]

                    pos1 = "LowBar"
                    pos2 = alliance_breakdown["position2"]
                    pos3 = alliance_breakdown["position3"]
                    pos4 = alliance_breakdown["position4"]
                    pos5 = alliance_breakdown["position5"]
                    positions = [pos1, pos2, pos3, pos4, pos5]

                    for pos_idx, pos in enumerate(positions):
                        defense_opportunities[pos] += 1
                        if (
                            alliance_breakdown[
                                "position{}crossings".format(pos_idx + 1)
                            ]
                            == 2
                        ):
                            defense_damaged[pos] += 1

                    breaches += 1 if alliance_breakdown["teleopDefensesBreached"] else 0
                    high_goals += (
                        alliance_breakdown["autoBouldersHigh"]
                        + alliance_breakdown["teleopBouldersHigh"]
                    )
                    low_goals += (
                        alliance_breakdown["autoBouldersLow"]
                        + alliance_breakdown["teleopBouldersLow"]
                    )
                    captures += 1 if alliance_breakdown["teleopTowerCaptured"] else 0

                    for tower_face in ["towerFaceA", "towerFaceB", "towerFaceC"]:
                        if alliance_breakdown[tower_face] == "Challenged":
                            challenges += 1
                        elif alliance_breakdown[tower_face] == "Scaled":
                            scales += 1
                    has_insights = True
                except Exception:
                    msg = "Event insights failed for {}".format(match.key.id())
                    # event.get() below should be cheap since it's backed by context cache
                    if match.event.get().event_type_enum in SEASON_EVENT_TYPES:
                        logging.warning(msg)
                    else:
                        logging.info(msg)
            finished_matches += 1

        if not has_insights:
            return None

        if finished_matches == 0:
            return {}

        opportunities_1x = 2 * finished_matches  # once per alliance
        opportunities_3x = 6 * finished_matches  # 3x per alliance
        event_insights = {
            "LowBar": [0, 0, 0],
            "A_ChevalDeFrise": [0, 0, 0],
            "A_Portcullis": [0, 0, 0],
            "B_Ramparts": [0, 0, 0],
            "B_Moat": [0, 0, 0],
            "C_SallyPort": [0, 0, 0],
            "C_Drawbridge": [0, 0, 0],
            "D_RoughTerrain": [0, 0, 0],
            "D_RockWall": [0, 0, 0],
            "average_high_goals": float(high_goals) / (2 * finished_matches),
            "average_low_goals": float(low_goals) / (2 * finished_matches),
            "breaches": [
                breaches,
                opportunities_1x,
                100.0 * float(breaches) / opportunities_1x,
            ],  # [# success, # opportunities, %]
            "scales": [
                scales,
                opportunities_3x,
                100.0 * float(scales) / opportunities_3x,
            ],
            "challenges": [
                challenges,
                opportunities_3x,
                100.0 * float(challenges) / opportunities_3x,
            ],
            "captures": [
                captures,
                opportunities_1x,
                100.0 * float(captures) / opportunities_1x,
            ],
            "average_win_score": float(winning_scores) / finished_matches,
            "average_win_margin": float(win_margins) / finished_matches,
            "average_score": float(total_scores) / (2 * finished_matches),
            "average_auto_score": float(auto_scores) / (2 * finished_matches),
            "average_crossing_score": float(crossing_scores) / (2 * finished_matches),
            "average_boulder_score": float(boulder_scores) / (2 * finished_matches),
            "average_tower_score": float(tower_scores) / (2 * finished_matches),
            "average_foul_score": float(foul_scores) / (2 * finished_matches),
            "high_score": list(high_score),  # [score, match key, match name]
        }
        for defense, opportunities in defense_opportunities.items():
            event_insights[defense] = [
                defense_damaged[defense],
                opportunities,
                100.0 * float(defense_damaged[defense]) / opportunities,
            ]  # [# damaged, # opportunities, %]

        return event_insights

    def get_prediction_relevant_stats(self) -> List[PredictionStatConfig]:
        return [
            PredictionStatConfig("score", 20, 10**2),
            PredictionStatConfig("auto_points", 20, 10**2),
            PredictionStatConfig("crossings", 0, 1**2),
            PredictionStatConfig("boulders", 0, 1**2),
        ]

    def prediction_brier_fields(self) -> List[Tuple[str, str, str]]:
        return [
            ("teleopDefensesBreached", "prob_breach", "breach"),
            ("teleopTowerCaptured", "prob_capture", "capture"),
        ]

    def ranking_tiebreaker_breakdown_field(self) -> Optional[str]:
        return "autoPoints"

    def ranking_tiebreaker_prediction_field(self) -> Optional[str]:
        return "auto_points"

    def ranking_sort_order_info(self) -> Optional[List[RankingSortOrderInfo]]:
        return [
            {"name": "Ranking Score", "precision": 0},
            {"name": "Auto", "precision": 0},
            {"name": "Scale/Challenge", "precision": 0},
            {"name": "Goals", "precision": 0},
            {"name": "Defense", "precision": 0},
        ]
