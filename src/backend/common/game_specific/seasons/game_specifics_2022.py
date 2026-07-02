from __future__ import annotations

import logging
import traceback
from typing import Any, Dict, List, Optional, Tuple

from backend.common.consts.alliance_color import (
    ALLIANCE_COLORS,
    AllianceColor,
)
from backend.common.consts.comp_level import CompLevel
from backend.common.consts.event_type import SEASON_EVENT_TYPES
from backend.common.frc_api.types import ScoreDetailModelAlliance2022
from backend.common.game_specific.base import (
    PredictionStatConfig,
    TCriteria,
    TotalPointsScoreBonusRpGameConfig,
)
from backend.common.models.event_insights import EventInsights
from backend.common.models.match import Match
from backend.common.models.ranking_sort_order_info import RankingSortOrderInfo


class GameSpecifics2022(
    TotalPointsScoreBonusRpGameConfig[ScoreDetailModelAlliance2022]
):
    SCORE_BREAKDOWN_MODEL = ScoreDetailModelAlliance2022
    BONUS_RP_BREAKDOWN_FIELDS = ("cargoBonusRankingPoint", "hangarBonusRankingPoint")
    BONUS_RP_PREDICTION_FIELDS = ("prob_cargo_bonus", "prob_hangar_bonus")

    def tiebreak_criteria(
        self, red: ScoreDetailModelAlliance2022, blue: ScoreDetailModelAlliance2022
    ) -> List[TCriteria]:
        tiebreakers: List[TCriteria] = []

        # Cumulative FOUL and TECH FOUL points due to opponent rule violations
        if "foulPoints" in red and "foulPoints" in blue:
            tiebreakers.append((red["foulPoints"], blue["foulPoints"]))
        else:
            tiebreakers.append(None)

        # Cumulative HANGAR points
        if "endgamePoints" in red and "endgamePoints" in blue:
            tiebreakers.append((red["endgamePoints"], blue["endgamePoints"]))
        else:
            tiebreakers.append(None)

        # Cumulative AUTO TAXI + CARGO points
        if "autoPoints" in red and "autoPoints" in blue:
            tiebreakers.append((red["autoPoints"], blue["autoPoints"]))
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

        qual_insights = self._calculate_event_insights_2022_helper(qual_matches)
        playoff_insights = self._calculate_event_insights_2022_helper(playoff_matches)

        return {
            "qual": qual_insights,
            "playoff": playoff_insights,
        }

    def _calculate_event_insights_2022_helper(
        self, matches: List[Match]
    ) -> Optional[Dict[str, Any]]:
        # Auto
        taxi_count = 0
        auto_lower_cargo_count = 0
        auto_upper_cargo_count = 0
        quintet_count = 0

        taxi_points = 0
        cargo_points_auto = 0
        points_auto = 0

        # Teleop
        teleop_lower_cargo_count = 0
        teleop_upper_cargo_count = 0
        low_climb_count = 0
        mid_climb_count = 0
        high_climb_count = 0
        traversal_climb_count = 0

        cargo_points_teleop = 0
        points_teleop = 0
        endgame_points = 0

        # Overall
        cargo_bonus_count = 0
        hangar_bonus_count = 0
        unicorn_matches = 0
        winning_scores = 0
        win_margins = 0
        total_cargo_points = 0
        total_scores = 0
        foul_scores = 0
        high_score: Tuple[int, str, str] = (0, "", "")

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
            if score_breakdown is None:
                continue

            for alliance_color in ALLIANCE_COLORS:
                try:
                    alliance_breakdown = score_breakdown[alliance_color]

                    # Auto Points
                    taxi_points += alliance_breakdown["autoTaxiPoints"]
                    cargo_points_auto += alliance_breakdown["autoCargoPoints"]
                    points_auto += alliance_breakdown["autoPoints"]

                    # Teleop Points
                    endgame_points += alliance_breakdown["endgamePoints"]
                    cargo_points_teleop += alliance_breakdown["teleopCargoPoints"]
                    points_teleop += alliance_breakdown["teleopPoints"]

                    # Counts
                    for i in range(3):
                        init_line = "taxiRobot{}".format(i + 1)
                        if alliance_breakdown[init_line] == "Yes":
                            taxi_count += 1

                        endgame = "endgameRobot{}".format(i + 1)
                        if alliance_breakdown[endgame] == "Traversal":
                            traversal_climb_count += 1
                        elif alliance_breakdown[endgame] == "High":
                            high_climb_count += 1
                        elif alliance_breakdown[endgame] == "Mid":
                            mid_climb_count += 1
                        elif alliance_breakdown[endgame] == "Low":
                            low_climb_count += 1

                    auto_lower_cargo_count += (
                        alliance_breakdown["autoCargoLowerNear"]
                        + alliance_breakdown["autoCargoLowerFar"]
                        + alliance_breakdown["autoCargoLowerRed"]
                        + alliance_breakdown["autoCargoLowerBlue"]
                    )
                    auto_upper_cargo_count += (
                        alliance_breakdown["autoCargoUpperNear"]
                        + alliance_breakdown["autoCargoUpperFar"]
                        + alliance_breakdown["autoCargoUpperRed"]
                        + alliance_breakdown["autoCargoUpperBlue"]
                    )
                    quintet_count += 1 if alliance_breakdown["quintetAchieved"] else 0
                    teleop_lower_cargo_count += (
                        alliance_breakdown["teleopCargoLowerNear"]
                        + alliance_breakdown["teleopCargoLowerFar"]
                        + alliance_breakdown["teleopCargoLowerRed"]
                        + alliance_breakdown["teleopCargoLowerBlue"]
                    )
                    teleop_upper_cargo_count += (
                        alliance_breakdown["teleopCargoUpperNear"]
                        + alliance_breakdown["teleopCargoUpperFar"]
                        + alliance_breakdown["teleopCargoUpperRed"]
                        + alliance_breakdown["teleopCargoUpperBlue"]
                    )

                    cargo_bonus_count += (
                        1 if alliance_breakdown["cargoBonusRankingPoint"] else 0
                    )
                    hangar_bonus_count += (
                        1 if alliance_breakdown["hangarBonusRankingPoint"] else 0
                    )
                    total_cargo_points += (
                        alliance_breakdown["autoCargoPoints"]
                        + alliance_breakdown["teleopCargoPoints"]
                    )

                    alliance_win = alliance_color == match.winning_alliance
                    unicorn_matches += (
                        1
                        if alliance_win
                        and alliance_breakdown["cargoBonusRankingPoint"]
                        and alliance_breakdown["hangarBonusRankingPoint"]
                        else 0
                    )
                    foul_scores += alliance_breakdown["foulPoints"]
                    has_insights = True
                except Exception as e:
                    msg = "Event insights failed for {}: {}".format(match.key.id(), e)
                    # event.get() below should be cheap since it's backed by context cache
                    if match.event.get().event_type_enum in SEASON_EVENT_TYPES:
                        logging.warning(msg)
                        logging.warning(traceback.format_exc())
                    else:
                        logging.info(msg)
            finished_matches += 1

        if not has_insights:
            return None

        if finished_matches == 0:
            return {}

        opportunities_1x = 2 * finished_matches
        opportunities_3x = 6 * finished_matches
        event_insights = {
            # Auto
            "taxi_count": [
                taxi_count,
                opportunities_3x,
                100.0 * float(taxi_count) / opportunities_3x,
            ],
            "average_taxi_points": float(taxi_points) / opportunities_1x,
            "average_lower_cargo_count_auto": float(auto_lower_cargo_count)
            / opportunities_1x,
            "average_upper_cargo_count_auto": float(auto_upper_cargo_count)
            / opportunities_1x,
            "average_cargo_count_auto": float(
                auto_lower_cargo_count + auto_upper_cargo_count
            )
            / opportunities_1x,
            "quintet_count": [
                quintet_count,
                opportunities_1x,
                100.0 * float(quintet_count) / opportunities_1x,
            ],
            "average_cargo_points_auto": float(cargo_points_auto) / opportunities_1x,
            "average_points_auto": float(points_auto) / opportunities_1x,
            # Teleop
            "average_lower_cargo_count_teleop": float(teleop_lower_cargo_count)
            / opportunities_1x,
            "average_upper_cargo_count_teleop": float(teleop_upper_cargo_count)
            / opportunities_1x,
            "average_cargo_count_teleop": float(
                teleop_lower_cargo_count + teleop_upper_cargo_count
            )
            / opportunities_1x,
            "average_cargo_points_teleop": float(cargo_points_teleop)
            / opportunities_1x,
            "low_climb_count": [
                low_climb_count,
                opportunities_3x,
                100.0 * float(low_climb_count) / opportunities_3x,
            ],
            "mid_climb_count": [
                mid_climb_count,
                opportunities_3x,
                100.0 * float(mid_climb_count) / opportunities_3x,
            ],
            "high_climb_count": [
                high_climb_count,
                opportunities_3x,
                100.0 * float(high_climb_count) / opportunities_3x,
            ],
            "traversal_climb_count": [
                traversal_climb_count,
                opportunities_3x,
                100.0 * float(traversal_climb_count) / opportunities_3x,
            ],
            "average_endgame_points": float(endgame_points) / opportunities_1x,
            "average_points_teleop": float(points_teleop) / opportunities_1x,
            # Overall
            "cargo_bonus_rp": [
                cargo_bonus_count,
                opportunities_1x,
                100.0 * float(cargo_bonus_count) / opportunities_1x,
            ],
            "hangar_bonus_rp": [
                hangar_bonus_count,
                opportunities_1x,
                100.0 * float(hangar_bonus_count) / opportunities_1x,
            ],
            "unicorn_matches": [
                unicorn_matches,
                opportunities_1x,
                100.0 * float(unicorn_matches) / opportunities_1x,
            ],
            "average_win_score": float(winning_scores) / finished_matches,
            "average_win_margin": float(win_margins) / finished_matches,
            "average_score": float(total_scores) / opportunities_1x,
            "average_lower_cargo_count": float(
                auto_lower_cargo_count + teleop_lower_cargo_count
            )
            / opportunities_1x,
            "average_upper_cargo_count": float(
                auto_upper_cargo_count + teleop_upper_cargo_count
            )
            / opportunities_1x,
            "average_cargo_count": float(
                auto_lower_cargo_count
                + teleop_lower_cargo_count
                + auto_upper_cargo_count
                + teleop_upper_cargo_count
            )
            / opportunities_1x,
            "average_cargo_points": float(cargo_points_auto + cargo_points_teleop)
            / opportunities_1x,
            "average_foul_score": float(foul_scores) / opportunities_1x,
            "high_score": list(high_score),
        }
        return event_insights

    def get_prediction_relevant_stats(self) -> List[PredictionStatConfig]:
        return [
            PredictionStatConfig("score", 0, 20**2),
            PredictionStatConfig("cargo_scored", 0, 10**2),
            PredictionStatConfig("endgame_points", 0, 10**2),
        ]

    def ranking_sort_order_info(self) -> Optional[List[RankingSortOrderInfo]]:
        return [
            {"name": "Ranking Score", "precision": 2},
            {"name": "Avg Match", "precision": 2},
            {"name": "Avg Hangar", "precision": 2},
            {"name": "Avg Taxi + Auto Cargo", "precision": 2},
        ]

    def round_robin_tiebreak_keys(self) -> List[str]:
        return ["endgamePoints", "autoPoints"]

    def round_robin_tiebreaker_names(self) -> List[str]:
        return ["Hangar Points", "Auto Taxi/Cargo Points"]
