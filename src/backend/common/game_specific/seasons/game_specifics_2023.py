from __future__ import annotations

import logging
import traceback
from typing import Any, Dict, List, Optional, Tuple

from backend.common.consts.alliance_color import (
    ALLIANCE_COLORS,
    AllianceColor,
    OPPONENT,
)
from backend.common.consts.comp_level import CompLevel
from backend.common.consts.event_type import SEASON_EVENT_TYPES
from backend.common.frc_api.types import ScoreDetailModelAlliance2023
from backend.common.game_specific.base import (
    PredictionStatConfig,
    StatAccessor,
    TCriteria,
    TotalPointsScoreBonusRpGameConfig,
)
from backend.common.models.event_insights import EventInsights
from backend.common.models.match import Match
from backend.common.models.ranking_sort_order_info import RankingSortOrderInfo


class GameSpecifics2023(
    TotalPointsScoreBonusRpGameConfig[ScoreDetailModelAlliance2023]
):
    SCORE_BREAKDOWN_MODEL = ScoreDetailModelAlliance2023
    BONUS_RP_BREAKDOWN_FIELDS = (
        "sustainabilityBonusAchieved",
        "activationBonusAchieved",
    )
    EXTRA_SCORE_BREAKDOWN_KEYS = frozenset(["tba_extraRp1", "tba_extraRp2"])
    BONUS_RP_PREDICTION_FIELDS = (
        "prob_sustainability_bonus",
        "prob_activation_bonus",
    )

    def tiebreak_criteria(
        self, red: ScoreDetailModelAlliance2023, blue: ScoreDetailModelAlliance2023
    ) -> List[TCriteria]:
        tiebreakers: List[TCriteria] = []

        # TECH FOUL points due to opponent rule violations
        # Since tech foul points are not provided, we use the count instead.
        if "techFoulCount" in red and "techFoulCount" in blue:
            tiebreakers.append((blue["techFoulCount"], red["techFoulCount"]))
        else:
            tiebreakers.append(None)

        # ALLIANCE CHARGE STATION points
        if "totalChargeStationPoints" in red and "totalChargeStationPoints" in blue:
            tiebreakers.append(
                (
                    red["totalChargeStationPoints"],
                    blue["totalChargeStationPoints"],
                )
            )
        else:
            tiebreakers.append(None)

        # ALLIANCE AUTO points
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

        qual_insights = self._calculate_event_insights_2023_helper(qual_matches)
        playoff_insights = self._calculate_event_insights_2023_helper(playoff_matches)

        return {
            "qual": qual_insights,
            "playoff": playoff_insights,
        }

    def _calculate_event_insights_2023_helper(
        self, matches: List[Match]
    ) -> Optional[Dict[str, Any]]:
        # Auto
        mobility_count = 0
        auto_top_count = 0
        auto_mid_count = 0
        auto_bot_count = 0
        auto_docked_count = 0
        auto_engaged_count = 0

        mobility_points = 0
        auto_piece_points = 0
        auto_charge_station_points = 0
        points_auto = 0

        # Teleop
        teleop_top_count = 0
        teleop_mid_count = 0
        teleop_bot_count = 0
        teleop_docked_count = 0
        teleop_engaged_count = 0
        coopertition_count = 0

        teleop_piece_points = 0
        park_points = 0
        teleop_charge_station_points = 0
        points_teleop = 0

        # Overall
        link_points = 0
        sustainability_bonus_count = 0
        activation_bonus_count = 0
        unicorn_matches = 0
        winning_scores = 0
        win_margins = 0
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
                    mobility_points += alliance_breakdown["autoMobilityPoints"]
                    auto_piece_points += alliance_breakdown["autoGamePiecePoints"]
                    auto_charge_station_points += alliance_breakdown[
                        "autoChargeStationPoints"
                    ]
                    points_auto += alliance_breakdown["autoPoints"]

                    # Teleop Points
                    teleop_piece_points += alliance_breakdown["teleopGamePiecePoints"]
                    park_points += alliance_breakdown["endGameParkPoints"]
                    teleop_charge_station_points += alliance_breakdown[
                        "endGameChargeStationPoints"
                    ]
                    points_teleop += alliance_breakdown["teleopPoints"]

                    # Overall Points
                    link_points += alliance_breakdown["linkPoints"]

                    # Counts
                    for i in range(3):
                        if alliance_breakdown["mobilityRobot{}".format(i + 1)] == "Yes":
                            mobility_count += 1

                        if (
                            alliance_breakdown[
                                "endGameChargeStationRobot{}".format(i + 1)
                            ]
                            == "Docked"
                        ):
                            teleop_docked_count += 1
                            if alliance_breakdown["endGameBridgeState"] == "Level":
                                teleop_engaged_count += 1

                    if alliance_breakdown["autoDocked"]:
                        auto_docked_count += 1
                        if alliance_breakdown["autoBridgeState"] == "Level":
                            auto_engaged_count += 1

                    auto_top_count += sum(
                        x != "None" for x in alliance_breakdown["autoCommunity"]["T"]
                    )
                    auto_mid_count += sum(
                        x != "None" for x in alliance_breakdown["autoCommunity"]["M"]
                    )
                    auto_bot_count += sum(
                        x != "None" for x in alliance_breakdown["autoCommunity"]["B"]
                    )

                    teleop_top_count += sum(
                        x != "None" for x in alliance_breakdown["teleopCommunity"]["T"]
                    )
                    teleop_mid_count += sum(
                        x != "None" for x in alliance_breakdown["teleopCommunity"]["M"]
                    )
                    teleop_bot_count += sum(
                        x != "None" for x in alliance_breakdown["teleopCommunity"]["B"]
                    )

                    coopertition_count += (
                        1 if alliance_breakdown["coopertitionCriteriaMet"] else 0
                    )
                    sustainability_bonus_count += (
                        1 if alliance_breakdown["sustainabilityBonusAchieved"] else 0
                    )
                    activation_bonus_count += (
                        1 if alliance_breakdown["activationBonusAchieved"] else 0
                    )

                    alliance_win = alliance_color == match.winning_alliance
                    unicorn_matches += (
                        1
                        if alliance_win
                        and alliance_breakdown["sustainabilityBonusAchieved"]
                        and alliance_breakdown["activationBonusAchieved"]
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
            "mobility_count": [
                mobility_count,
                opportunities_3x,
                100.0 * float(mobility_count) / opportunities_3x,
            ],
            "auto_docked_count": [
                auto_docked_count,
                opportunities_1x,
                100.0 * float(auto_docked_count) / opportunities_1x,
            ],
            "auto_engaged_count": [
                auto_engaged_count,
                opportunities_1x,
                100.0 * float(auto_engaged_count) / opportunities_1x,
            ],
            "average_mobility_points": float(mobility_points) / opportunities_1x,
            "average_piece_points_auto": float(auto_piece_points) / opportunities_1x,
            "average_charge_station_points_auto": float(auto_charge_station_points)
            / opportunities_1x,
            "average_points_auto": float(points_auto) / opportunities_1x,
            # Teleop
            "average_piece_points_teleop": float(teleop_piece_points)
            / opportunities_1x,
            "average_park_points": float(park_points) / opportunities_1x,
            "average_charge_station_points_teleop": float(teleop_charge_station_points)
            / opportunities_1x,
            "average_points_teleop": float(points_teleop) / opportunities_1x,
            # Overall
            "average_link_points": float(link_points) / opportunities_1x,
            "coopertition": [
                coopertition_count,
                opportunities_1x,
                100.0 * float(coopertition_count) / opportunities_1x,
            ],
            "sustainability_bonus_rp": [
                sustainability_bonus_count,
                opportunities_1x,
                100.0 * float(sustainability_bonus_count) / opportunities_1x,
            ],
            "activation_bonus_rp": [
                activation_bonus_count,
                opportunities_1x,
                100.0 * float(activation_bonus_count) / opportunities_1x,
            ],
            "unicorn_matches": [
                unicorn_matches,
                opportunities_1x,
                100.0 * float(unicorn_matches) / opportunities_1x,
            ],
            "average_win_score": float(winning_scores) / finished_matches,
            "average_win_margin": float(win_margins) / finished_matches,
            "average_score": float(total_scores) / opportunities_1x,
            "average_foul_score": float(foul_scores) / opportunities_1x,
            "high_score": list(high_score),
        }
        return event_insights

    def get_manual_coprs(self) -> Dict[str, StatAccessor]:
        return {
            "Total Game Piece Count": lambda match, color: (
                match.score_breakdown[color].get("teleopGamePieceCount", 0)
                + match.score_breakdown[color].get("extraGamePieceCount", 0)
            ),
            "Total Game Piece Points": lambda match, color: (
                match.score_breakdown[color].get("autoGamePiecePoints", 0)
                + match.score_breakdown[color].get("teleopGamePiecePoints", 0)
            ),
            "Foul Count Received": lambda match, color: (
                match.score_breakdown[OPPONENT[color]].get("foulCount", 0)
            ),
            "Foul Points Received": lambda match, color: (
                match.score_breakdown[OPPONENT[color]].get("foulPoints", 0)
            ),
            "Total Points Less Fouls": lambda match, color: (
                match.score_breakdown[color].get("totalPoints", 0)
                - match.score_breakdown[color].get("foulPoints", 0)
            ),
            "Total Cones Scored": lambda match, color: (
                sum(
                    [
                        match.score_breakdown[color]["teleopCommunity"]["B"].count(
                            "Cone"
                        ),
                        match.score_breakdown[color]["teleopCommunity"]["M"].count(
                            "Cone"
                        ),
                        match.score_breakdown[color]["teleopCommunity"]["T"].count(
                            "Cone"
                        ),
                    ]
                )
            ),
            "Total Cubes Scored": lambda match, color: (
                sum(
                    [
                        match.score_breakdown[color]["teleopCommunity"]["B"].count(
                            "Cube"
                        ),
                        match.score_breakdown[color]["teleopCommunity"]["M"].count(
                            "Cube"
                        ),
                        match.score_breakdown[color]["teleopCommunity"]["T"].count(
                            "Cube"
                        ),
                    ]
                )
            ),
        }

    def get_prediction_relevant_stats(self) -> List[PredictionStatConfig]:
        return [
            PredictionStatConfig("score", 0, 20**2),
            PredictionStatConfig("links", 0, 3**2),
            PredictionStatConfig("charge_station_points", 0, 10**2),
        ]

    def ranking_sort_order_info(self) -> Optional[List[RankingSortOrderInfo]]:
        return [
            {"name": "Ranking Score", "precision": 2},
            {"name": "Avg Match", "precision": 2},
            {"name": "Avg Charge Station", "precision": 2},
            {"name": "Avg Auto", "precision": 2},
        ]
