from __future__ import annotations

import logging
import traceback
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

from backend.common.consts.alliance_color import (
    ALLIANCE_COLORS,
    AllianceColor,
)
from backend.common.consts.comp_level import CompLevel
from backend.common.consts.event_type import SEASON_EVENT_TYPES
from backend.common.frc_api.types import ScoreDetailModelAlliance2019
from backend.common.game_specific.base import (
    PredictionStatConfig,
    StatAccessor,
    TCriteria,
    TotalPointsScoreBonusRpGameConfig,
)
from backend.common.models.event_insights import EventInsights
from backend.common.models.match import Match
from backend.common.models.ranking_sort_order_info import RankingSortOrderInfo


class GameSpecifics2019(
    TotalPointsScoreBonusRpGameConfig[ScoreDetailModelAlliance2019]
):
    SCORE_BREAKDOWN_MODEL = ScoreDetailModelAlliance2019
    BONUS_RP_BREAKDOWN_FIELDS = (
        "completeRocketRankingPoint",
        "habDockingRankingPoint",
    )
    BONUS_RP_PREDICTION_FIELDS = ("prob_complete_rocket", "prob_hab_docking")

    def tiebreak_criteria(
        self, red: ScoreDetailModelAlliance2019, blue: ScoreDetailModelAlliance2019
    ) -> List[TCriteria]:
        tiebreakers: List[TCriteria] = []

        # Greater number of FOUL points awarded (i.e. the ALLIANCE that played the cleaner MATCH)
        if "foulPoints" in red and "foulPoints" in blue:
            tiebreakers.append((red["foulPoints"], blue["foulPoints"]))
        else:
            tiebreakers.append(None)

        # Cumulative sum of scored CARGO points
        if "cargoPoints" in red and "cargoPoints" in blue:
            tiebreakers.append((red["cargoPoints"], blue["cargoPoints"]))
        else:
            tiebreakers.append(None)

        # Cumulative sum of scored HATCH PANEL points
        if "hatchPanelPoints" in red and "hatchPanelPoints" in blue:
            tiebreakers.append((red["hatchPanelPoints"], blue["hatchPanelPoints"]))
        else:
            tiebreakers.append(None)

        # Cumulative sum of scored HAB CLIMB points
        if "habClimbPoints" in red and "habClimbPoints" in blue:
            tiebreakers.append((red["habClimbPoints"], blue["habClimbPoints"]))
        else:
            tiebreakers.append(None)

        # Cumulative sum of scored SANDSTORM BONUS points
        if "sandStormBonusPoints" in red and "sandStormBonusPoints" in blue:
            tiebreakers.append(
                (
                    red["sandStormBonusPoints"],
                    blue["sandStormBonusPoints"],
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

        qual_insights = self._calculate_event_insights_2019_helper(qual_matches)
        playoff_insights = self._calculate_event_insights_2019_helper(playoff_matches)

        return {
            "qual": qual_insights,
            "playoff": playoff_insights,
        }

    def _calculate_event_insights_2019_helper(
        self, matches: List[Match]
    ) -> Optional[Dict[str, Any]]:
        # Auto
        sandstorm_bonus_auto = 0
        points_auto = 0

        # Teleop
        hab_climb_teleop = 0
        points_teleop = 0

        # Overall
        cross_hab_line_count = 0
        cross_hab_line_sandstorm_count = 0
        complete_1_rocket_count = 0
        complete_2_rockets_count = 0

        cargo_ship_hatch_panel_preload_count = [0] * 6  # 0 starts from far left
        cargo_ship_cargo_preload_count = [0] * 6  # 0 starts from far left
        cargo_ship_hatch_panel_count = [0] * 8  # 0 starts from far left
        cargo_ship_cargo_count = [0] * 8  # 0 starts from far left
        rocket_hatch_panel_count = defaultdict(int)
        rocket_cargo_count = defaultdict(int)
        hatch_panel_points = 0
        cargo_points = 0
        level1_climb_count = 0
        level2_climb_count = 0
        level3_climb_count = 0

        # kpa_achieved = 0
        rocket_rp_achieved = 0
        climb_rp_achieved = 0
        unicorn_matches = 0

        winning_scores = 0
        win_margins = 0
        total_scores = 0
        foul_scores = 0
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
                isRed = alliance_color == AllianceColor.RED
                try:
                    alliance_breakdown = score_breakdown[alliance_color]

                    # Auto
                    sandstorm_bonus_auto += alliance_breakdown["sandStormBonusPoints"]
                    points_auto += alliance_breakdown["autoPoints"]

                    # Teleop
                    hab_climb_teleop += alliance_breakdown["habClimbPoints"]
                    points_teleop += alliance_breakdown["teleopPoints"]

                    # Overall
                    for i in range(3):
                        hab_line = "habLineRobot{}".format(i + 1)
                        if alliance_breakdown[hab_line] == "CrossedHabLineInTeleop":
                            cross_hab_line_count += 1
                        elif (
                            alliance_breakdown[hab_line] == "CrossedHabLineInSandstorm"
                        ):
                            cross_hab_line_count += 1
                            cross_hab_line_sandstorm_count += 1

                        hab_climb = "endgameRobot{}".format(i + 1)
                        if alliance_breakdown[hab_climb] == "HabLevel1":
                            level1_climb_count += 1
                        elif alliance_breakdown[hab_climb] == "HabLevel2":
                            level2_climb_count += 1
                        elif alliance_breakdown[hab_climb] == "HabLevel3":
                            level3_climb_count += 1

                    complete_1_rocket_count += (
                        1
                        if alliance_breakdown["completedRocketNear"]
                        or alliance_breakdown["completedRocketFar"]
                        else 0
                    )
                    complete_2_rockets_count += (
                        1
                        if alliance_breakdown["completedRocketNear"]
                        and alliance_breakdown["completedRocketFar"]
                        else 0
                    )

                    if alliance_breakdown["preMatchBay1"] == "Panel":
                        cargo_ship_hatch_panel_preload_count[0 if isRed else 5] += 1
                    else:
                        cargo_ship_cargo_preload_count[0 if isRed else 5] += 1
                    if alliance_breakdown["preMatchBay2"] == "Panel":
                        cargo_ship_hatch_panel_preload_count[1 if isRed else 4] += 1
                    else:
                        cargo_ship_cargo_preload_count[1 if isRed else 4] += 1
                    if alliance_breakdown["preMatchBay3"] == "Panel":
                        cargo_ship_hatch_panel_preload_count[2 if isRed else 3] += 1
                    else:
                        cargo_ship_cargo_preload_count[2 if isRed else 3] += 1
                    if alliance_breakdown["preMatchBay6"] == "Panel":
                        cargo_ship_hatch_panel_preload_count[3 if isRed else 2] += 1
                    else:
                        cargo_ship_cargo_preload_count[3 if isRed else 2] += 1
                    if alliance_breakdown["preMatchBay7"] == "Panel":
                        cargo_ship_hatch_panel_preload_count[4 if isRed else 1] += 1
                    else:
                        cargo_ship_cargo_preload_count[4 if isRed else 1] += 1
                    if alliance_breakdown["preMatchBay8"] == "Panel":
                        cargo_ship_hatch_panel_preload_count[5 if isRed else 0] += 1
                    else:
                        cargo_ship_cargo_preload_count[5 if isRed else 0] += 1

                    for i in range(8):
                        idx = i if isRed else 7 - i
                        bay = "bay{}".format(i + 1)
                        cargo_ship_hatch_panel_count[idx] += (
                            1 if "Panel" in alliance_breakdown[bay] else 0
                        )
                        cargo_ship_cargo_count[idx] += (
                            1 if "Cargo" in alliance_breakdown[bay] else 0
                        )

                    for LRSide in ["Left", "Right"]:  # Relative to Field
                        for NFSide in ["Near", "Far"]:  # Relative to Field
                            low = "low{}Rocket{}".format(LRSide, NFSide)
                            mid = "mid{}Rocket{}".format(LRSide, NFSide)
                            top = "top{}Rocket{}".format(LRSide, NFSide)

                            # Get alliance-relative sides
                            if NFSide == "Near" and LRSide == "Left":
                                alLRSide = "Left" if isRed else "Right"
                                alNFSide = "Near" if isRed else "Far"
                            elif NFSide == "Near" and LRSide == "Right":
                                alLRSide = "Left" if isRed else "Right"
                                alNFSide = "Far" if isRed else "Near"
                            elif NFSide == "Far" and LRSide == "Left":
                                alLRSide = "Right" if isRed else "Left"
                                alNFSide = "Far" if isRed else "Near"
                            elif NFSide == "Far" and LRSide == "Right":
                                alLRSide = "Right" if isRed else "Left"
                                alNFSide = "Near" if isRed else "Far"
                            else:
                                alLRSide = ""
                                alNFSide = ""

                            rocket_hatch_panel_count[
                                "low{}{}".format(alLRSide, alNFSide)
                            ] += (1 if "Panel" in alliance_breakdown[low] else 0)
                            rocket_hatch_panel_count[
                                "mid{}{}".format(alLRSide, alNFSide)
                            ] += (1 if "Panel" in alliance_breakdown[mid] else 0)
                            rocket_hatch_panel_count[
                                "top{}{}".format(alLRSide, alNFSide)
                            ] += (1 if "Panel" in alliance_breakdown[top] else 0)
                            rocket_cargo_count[
                                "low{}{}".format(alLRSide, alNFSide)
                            ] += (1 if "Cargo" in alliance_breakdown[low] else 0)
                            rocket_cargo_count[
                                "mid{}{}".format(alLRSide, alNFSide)
                            ] += (1 if "Cargo" in alliance_breakdown[mid] else 0)
                            rocket_cargo_count[
                                "top{}{}".format(alLRSide, alNFSide)
                            ] += (1 if "Cargo" in alliance_breakdown[top] else 0)

                    hatch_panel_points += alliance_breakdown["hatchPanelPoints"]
                    cargo_points += alliance_breakdown["cargoPoints"]

                    completed_rocket = (
                        alliance_breakdown["completedRocketNear"]
                        or alliance_breakdown["completedRocketFar"]
                    )
                    alliance_rocket_rp_achieved = (
                        alliance_breakdown["completeRocketRankingPoint"]
                        or completed_rocket
                    )
                    alliance_climb_rp_achieved = alliance_breakdown[
                        "habDockingRankingPoint"
                    ] or (alliance_breakdown["habClimbPoints"] >= 15)
                    rocket_rp_achieved += 1 if alliance_rocket_rp_achieved else 0
                    climb_rp_achieved += 1 if alliance_climb_rp_achieved else 0
                    alliance_win = alliance_color == match.winning_alliance
                    unicorn_matches += (
                        1
                        if (
                            alliance_win
                            and alliance_rocket_rp_achieved
                            and alliance_climb_rp_achieved
                        )
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
        average_rocket_hatch_panel_count = {}
        for key, value in rocket_hatch_panel_count.items():
            average_rocket_hatch_panel_count[key] = (
                100 * float(value) / opportunities_1x
            )
        average_rocket_cargo_count = {}
        for key, value in rocket_cargo_count.items():
            average_rocket_cargo_count[key] = 100 * float(value) / opportunities_1x
        event_insights = {
            # Auto
            "average_sandstorm_bonus_auto": float(sandstorm_bonus_auto)
            / (2 * finished_matches),
            "average_points_auto": float(points_auto) / (2 * finished_matches),
            # Teleop
            "average_hab_climb_teleop": float(hab_climb_teleop)
            / (2 * finished_matches),
            "average_points_teleop": float(points_teleop) / (2 * finished_matches),
            # Overall
            "cross_hab_line_count": [
                cross_hab_line_count,
                opportunities_3x,
                100.0 * float(cross_hab_line_count) / opportunities_3x,
            ],
            "cross_hab_line_sandstorm_count": [
                cross_hab_line_sandstorm_count,
                opportunities_3x,
                100.0 * float(cross_hab_line_sandstorm_count) / opportunities_3x,
            ],
            "level1_climb_count": [
                level1_climb_count,
                opportunities_3x,
                100.0 * float(level1_climb_count) / opportunities_3x,
            ],
            "level2_climb_count": [
                level2_climb_count,
                opportunities_3x,
                100.0 * float(level2_climb_count) / opportunities_3x,
            ],
            "level3_climb_count": [
                level3_climb_count,
                opportunities_3x,
                100.0 * float(level3_climb_count) / opportunities_3x,
            ],
            "complete_1_rocket_count": [
                complete_1_rocket_count,
                opportunities_1x,
                100.0 * float(complete_1_rocket_count) / opportunities_1x,
            ],
            "complete_2_rockets_count": [
                complete_2_rockets_count,
                opportunities_1x,
                100.0 * float(complete_2_rockets_count) / opportunities_1x,
            ],
            "average_cargo_ship_hatch_panel_preload_count": [
                100.0 * float(x) / opportunities_1x
                for x in cargo_ship_hatch_panel_preload_count
            ],
            "average_cargo_ship_cargo_preload_count": [
                100.0 * float(x) / opportunities_1x
                for x in cargo_ship_cargo_preload_count
            ],
            "average_cargo_ship_hatch_panel_count": [
                100.0 * float(x) / opportunities_1x
                for x in cargo_ship_hatch_panel_count
            ],
            "average_cargo_ship_cargo_count": [
                100.0 * float(x) / opportunities_1x for x in cargo_ship_cargo_count
            ],
            "average_rocket_hatch_panel_count": average_rocket_hatch_panel_count,
            "average_rocket_cargo_count": average_rocket_cargo_count,
            "average_hatch_panel_points": float(hatch_panel_points) / opportunities_1x,
            "average_cargo_points": float(cargo_points) / opportunities_1x,
            "rocket_rp_achieved": [
                rocket_rp_achieved,
                opportunities_1x,
                100.0 * float(rocket_rp_achieved) / opportunities_1x,
            ],
            "climb_rp_achieved": [
                climb_rp_achieved,
                opportunities_1x,
                100.0 * float(climb_rp_achieved) / opportunities_1x,
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
            "high_score": list(high_score),  # [score, match key, match name]
        }

        return event_insights

    def get_manual_coprs(self) -> Dict[str, StatAccessor]:
        return {
            "Cargo + Panel Points": lambda match, color: (
                match.score_breakdown[color].get("cargoPoints", 0)
                + match.score_breakdown[color].get("hatchPanelPoints", 0)
            )
        }

    def get_prediction_relevant_stats(self) -> List[PredictionStatConfig]:
        return [
            PredictionStatConfig("score", 10, 20**2),
            PredictionStatConfig("rocket_pieces_scored", 1, 3**2),
            PredictionStatConfig("hab_climb_points", 2, 3**2),
        ]

    def ranking_sort_order_info(self) -> Optional[List[RankingSortOrderInfo]]:
        return [
            {"name": "Ranking Score", "precision": 2},
            {"name": "Cargo", "precision": 0},
            {"name": "Hatch Panel", "precision": 0},
            {"name": "HAB Climb", "precision": 0},
            {"name": "Sandstorm Bonus", "precision": 0},
        ]

    def round_robin_tiebreak_keys(self) -> List[str]:
        return ["cargoPoints", "hatchPanelPoints"]

    def round_robin_tiebreaker_names(self) -> List[str]:
        return ["Cargo Points", "Hatch Panel Points"]
