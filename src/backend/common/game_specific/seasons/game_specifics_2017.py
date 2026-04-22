from __future__ import annotations

import logging
import traceback
from typing import Any, Dict, List, Optional, Tuple, TypedDict

from backend.common.consts.alliance_color import ALLIANCE_COLORS, AllianceColor
from backend.common.consts.comp_level import CompLevel
from backend.common.consts.event_type import SEASON_EVENT_TYPES
from backend.common.frc_api.types import ScoreDetailModelAlliance2017
from backend.common.game_specific.base import (
    PredictionStatConfig,
    TCriteria,
    TotalPointsScoreBonusRpGameConfig,
)
from backend.common.models.event_insights import EventInsights
from backend.common.models.match import Match
from backend.common.models.ranking_sort_order_info import RankingSortOrderInfo


class GameSpecifics2017(
    TotalPointsScoreBonusRpGameConfig[ScoreDetailModelAlliance2017]
):
    SCORE_BREAKDOWN_MODEL = ScoreDetailModelAlliance2017
    BONUS_RP_BREAKDOWN_FIELDS = ("kPaRankingPointAchieved", "rotorRankingPointAchieved")
    BONUS_RP_PREDICTION_FIELDS = ("prob_pressure", "prob_gears")

    def tiebreak_criteria(
        self, red: ScoreDetailModelAlliance2017, blue: ScoreDetailModelAlliance2017
    ) -> List[TCriteria]:
        tiebreakers: List[TCriteria] = []

        # Greater number of FOUL points awarded (i.e. the ALLIANCE that played the cleaner MATCH)
        if "foulPoints" in red and "foulPoints" in blue:
            tiebreakers.append((red["foulPoints"], blue["foulPoints"]))
        else:
            tiebreakers.append(None)

        # Cumulative sum of scored AUTO points
        if "autoPoints" in red and "autoPoints" in blue:
            tiebreakers.append((red["autoPoints"], blue["autoPoints"]))
        else:
            tiebreakers.append(None)

        # Cumulative ROTOR engagement score (AUTO and TELEOP)
        if (
            "autoRotorPoints" in red
            and "autoRotorPoints" in blue
            and "teleopRotorPoints" in red
            and "teleopRotorPoints" in blue
        ):
            red_rotor = red["autoRotorPoints"] + red["teleopRotorPoints"]
            blue_rotor = blue["autoRotorPoints"] + blue["teleopRotorPoints"]
            tiebreakers.append((red_rotor, blue_rotor))
        else:
            tiebreakers.append(None)

        # Cumulative TOUCHPAD score
        if "teleopTakeoffPoints" in red and "teleopTakeoffPoints" in blue:
            tiebreakers.append(
                (red["teleopTakeoffPoints"], blue["teleopTakeoffPoints"])
            )
        else:
            tiebreakers.append(None)

        # Total accumulated pressure
        if (
            "autoFuelPoints" in red
            and "autoFuelPoints" in blue
            and "teleopFuelPoints" in red
            and "teleopFuelPoints" in blue
        ):
            red_pressure = red["autoFuelPoints"] + red["teleopFuelPoints"]
            blue_pressure = blue["autoFuelPoints"] + blue["teleopFuelPoints"]
            tiebreakers.append((red_pressure, blue_pressure))
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

        qual_insights = self._calculate_event_insights_2017_helper(qual_matches)
        playoff_insights = self._calculate_event_insights_2017_helper(playoff_matches)

        return {
            "qual": qual_insights,
            "playoff": playoff_insights,
        }

    def _calculate_event_insights_2017_helper(
        self, matches: List[Match]
    ) -> Optional[Dict[str, Any]]:
        # Auto
        mobility_points_auto = 0
        rotor_points_auto = 0
        high_goals_auto = 0
        low_goals_auto = 0
        fuel_points_auto = 0
        points_auto = 0
        mobility_counts = 0

        # Teleop
        rotor_points_teleop = 0
        high_goals_teleop = 0
        low_goals_teleop = 0
        fuel_points_teleop = 0
        takeoff_points_teleop = 0
        points_teleop = 0
        takeoff_counts = 0

        # Overall
        rotor_1_engaged_auto = 0
        rotor_2_engaged_auto = 0
        rotor_1_engaged = 0
        rotor_2_engaged = 0
        rotor_3_engaged = 0
        rotor_4_engaged = 0
        rotor_points = 0
        high_goals = 0
        low_goals = 0
        fuel_points = 0

        kpa_achieved = 0
        unicorn_matches = 0

        winning_scores = 0
        win_margins = 0
        total_scores = 0
        foul_scores = 0
        high_kpa: Tuple[int, str, str] = (0, "", "")  # score, match key, match name
        high_score: Tuple[int, str, str] = (0, "", "")  # kpa, match key, match name

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

                    # High kPa
                    kpa = (
                        alliance_breakdown["autoFuelPoints"]
                        + alliance_breakdown["teleopFuelPoints"]
                    )
                    if kpa > high_kpa[0]:
                        high_kpa = (kpa, match.key_name, match.short_name)

                    # Auto
                    mobility_points_auto += alliance_breakdown["autoMobilityPoints"]
                    rotor_points_auto += alliance_breakdown["autoRotorPoints"]
                    fuel_points_auto += alliance_breakdown["autoFuelPoints"]
                    high_goals_auto += alliance_breakdown["autoFuelHigh"]
                    low_goals_auto += alliance_breakdown["autoFuelLow"]
                    points_auto += alliance_breakdown["autoPoints"]
                    for i in range(3):
                        mobility_counts += (
                            1
                            if alliance_breakdown["robot{}Auto".format(i + 1)]
                            == "Mobility"
                            else 0
                        )

                    # Teleop
                    rotor_points_teleop += alliance_breakdown["teleopRotorPoints"]
                    fuel_points_teleop += alliance_breakdown["teleopFuelPoints"]
                    high_goals_teleop += alliance_breakdown["teleopFuelHigh"]
                    low_goals_teleop += alliance_breakdown["teleopFuelLow"]
                    takeoff_points_teleop += alliance_breakdown["teleopTakeoffPoints"]
                    points_teleop += alliance_breakdown["teleopPoints"]
                    takeoff_counts += (
                        1
                        if alliance_breakdown["touchpadFar"] == "ReadyForTakeoff"
                        else 0
                    )
                    takeoff_counts += (
                        1
                        if alliance_breakdown["touchpadMiddle"] == "ReadyForTakeoff"
                        else 0
                    )
                    takeoff_counts += (
                        1
                        if alliance_breakdown["touchpadNear"] == "ReadyForTakeoff"
                        else 0
                    )

                    # Overall
                    rotor_1_engaged_auto += 1 if alliance_breakdown["rotor1Auto"] else 0
                    rotor_2_engaged_auto += 1 if alliance_breakdown["rotor2Auto"] else 0
                    rotor_1_engaged += 1 if alliance_breakdown["rotor1Engaged"] else 0
                    rotor_2_engaged += 1 if alliance_breakdown["rotor2Engaged"] else 0
                    rotor_3_engaged += 1 if alliance_breakdown["rotor3Engaged"] else 0
                    rotor_4_engaged += 1 if alliance_breakdown["rotor4Engaged"] else 0
                    rotor_points += (
                        alliance_breakdown["autoRotorPoints"]
                        + alliance_breakdown["teleopRotorPoints"]
                    )
                    high_goals += (
                        alliance_breakdown["autoFuelHigh"]
                        + alliance_breakdown["teleopFuelHigh"]
                    )
                    low_goals += (
                        alliance_breakdown["autoFuelLow"]
                        + alliance_breakdown["teleopFuelLow"]
                    )
                    fuel_points += (
                        alliance_breakdown["autoFuelPoints"]
                        + alliance_breakdown["teleopFuelPoints"]
                    )

                    kpa_bonus = (
                        alliance_breakdown["kPaRankingPointAchieved"]
                        or alliance_breakdown["kPaBonusPoints"] > 0
                    )
                    kpa_achieved += 1 if kpa_bonus else 0

                    alliance_win = alliance_color == match.winning_alliance
                    unicorn_matches += (
                        1
                        if alliance_win
                        and kpa_bonus
                        and alliance_breakdown["rotor4Engaged"]
                        else 0
                    )

                    foul_scores += alliance_breakdown["foulPoints"]
                    has_insights = True
                except Exception:
                    msg = "Event insights failed for {}".format(match.key.id())
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

        opportunities_1x = 2 * finished_matches  # once per alliance
        opportunities_3x = 6 * finished_matches  # 3x per alliance
        event_insights = {
            # Auto
            "average_mobility_points_auto": float(mobility_points_auto)
            / (2 * finished_matches),
            "average_rotor_points_auto": float(rotor_points_auto)
            / (2 * finished_matches),
            "average_fuel_points_auto": float(fuel_points_auto)
            / (2 * finished_matches),
            "average_high_goals_auto": float(high_goals_auto) / (2 * finished_matches),
            "average_low_goals_auto": float(low_goals_auto) / (2 * finished_matches),
            "average_points_auto": float(points_auto) / (2 * finished_matches),
            "mobility_counts": [
                mobility_counts,
                opportunities_3x,
                100.0 * float(mobility_counts) / opportunities_3x,
            ],
            # Teleop
            "average_rotor_points_teleop": float(rotor_points_teleop)
            / (2 * finished_matches),
            "average_fuel_points_teleop": float(fuel_points_teleop)
            / (2 * finished_matches),
            "average_high_goals_teleop": float(high_goals_teleop)
            / (2 * finished_matches),
            "average_low_goals_teleop": float(low_goals_teleop)
            / (2 * finished_matches),
            "average_takeoff_points_teleop": float(takeoff_points_teleop)
            / (2 * finished_matches),
            "average_points_teleop": float(points_teleop) / (2 * finished_matches),
            "takeoff_counts": [
                takeoff_counts,
                opportunities_3x,
                100.0 * float(takeoff_counts) / opportunities_3x,
            ],
            # Overall
            "average_rotor_points": float(rotor_points) / (2 * finished_matches),
            "average_fuel_points": float(fuel_points) / (2 * finished_matches),
            "average_high_goals": float(high_goals) / (2 * finished_matches),
            "average_low_goals": float(low_goals) / (2 * finished_matches),
            "rotor_1_engaged_auto": [
                rotor_1_engaged_auto,
                opportunities_1x,
                100.0 * float(rotor_1_engaged_auto) / opportunities_1x,
            ],
            "rotor_2_engaged_auto": [
                rotor_2_engaged_auto,
                opportunities_1x,
                100.0 * float(rotor_2_engaged_auto) / opportunities_1x,
            ],
            "rotor_1_engaged": [
                rotor_1_engaged,
                opportunities_1x,
                100.0 * float(rotor_1_engaged) / opportunities_1x,
            ],
            "rotor_2_engaged": [
                rotor_2_engaged,
                opportunities_1x,
                100.0 * float(rotor_2_engaged) / opportunities_1x,
            ],
            "rotor_3_engaged": [
                rotor_3_engaged,
                opportunities_1x,
                100.0 * float(rotor_3_engaged) / opportunities_1x,
            ],
            "rotor_4_engaged": [
                rotor_4_engaged,
                opportunities_1x,
                100.0 * float(rotor_4_engaged) / opportunities_1x,
            ],
            "kpa_achieved": [
                kpa_achieved,
                opportunities_1x,
                100.0 * float(kpa_achieved) / opportunities_1x,
            ],
            "unicorn_matches": [
                unicorn_matches,
                opportunities_1x,
                100.0 * float(unicorn_matches) / opportunities_1x,
            ],
            "average_win_score": float(winning_scores) / finished_matches,
            "average_win_margin": float(win_margins) / finished_matches,
            "average_score": float(total_scores) / (2 * finished_matches),
            "average_foul_score": float(foul_scores) / (2 * finished_matches),
            "high_score": list(high_score),  # [score, match key, match name]
            "high_kpa": list(high_kpa),  # [kpa, match key, match name]
        }

        return event_insights

    def get_prediction_relevant_stats(self) -> List[PredictionStatConfig]:
        return [
            PredictionStatConfig("score", 50, 30**2),
            PredictionStatConfig("pressure", 0, 1**2),
            PredictionStatConfig("gears", 0, 1**2),
        ]

    def prediction_brier_fields(self) -> List[Tuple[str, str, str]]:
        return [
            ("kPaRankingPointAchieved", "prob_pressure", "pressure"),
            ("rotorRankingPointAchieved", "prob_gears", "gears"),
        ]

    def ranking_sort_order_info(self) -> Optional[List[RankingSortOrderInfo]]:
        return [
            {"name": "Ranking Score", "precision": 2},
            {"name": "Match Points", "precision": 0},
            {"name": "Auto", "precision": 0},
            {"name": "Rotor", "precision": 0},
            {"name": "Touchpad", "precision": 0},
            {"name": "Pressure", "precision": 0},
        ]

    def round_robin_tiebreak_keys(self) -> List[str]:
        return ["totalPoints"]

    def round_robin_tiebreaker_names(self) -> List[str]:
        return ["Match Points"]


class _RankingBreakdown2017(TypedDict):
    kPaRankingPointAchieved: bool
    rotorRankingPointAchieved: bool


class _RankingPrediction2017(TypedDict):
    prob_pressure: float
    prob_gears: float
