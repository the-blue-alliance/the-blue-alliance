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
from backend.common.frc_api.types import ScoreDetailModelAlliance2020
from backend.common.game_specific.base import (
    PredictionStatConfig,
    TCriteria,
    TotalPointsScoreBonusRpGameConfig,
)
from backend.common.models.event_insights import EventInsights
from backend.common.models.match import Match
from backend.common.models.ranking_sort_order_info import RankingSortOrderInfo


class GameSpecifics2020(
    TotalPointsScoreBonusRpGameConfig[ScoreDetailModelAlliance2020]
):
    SCORE_BREAKDOWN_MODEL = ScoreDetailModelAlliance2020
    BONUS_RP_BREAKDOWN_FIELDS = (
        "shieldEnergizedRankingPoint",
        "shieldOperationalRankingPoint",
    )
    BONUS_RP_PREDICTION_FIELDS = ("prob_shield_energized", "prob_shield_operational")

    def tiebreak_criteria(
        self, red: ScoreDetailModelAlliance2020, blue: ScoreDetailModelAlliance2020
    ) -> List[TCriteria]:
        tiebreakers: List[TCriteria] = []

        # Cumulative FOUL and TECH FOUL points due to opponent rule violations
        if "foulPoints" in red and "foulPoints" in blue:
            tiebreakers.append((red["foulPoints"], blue["foulPoints"]))
        else:
            tiebreakers.append(None)

        # Cumulative AUTO points
        if "autoPoints" in red and "autoPoints" in blue:
            tiebreakers.append((red["autoPoints"], blue["autoPoints"]))
        else:
            tiebreakers.append(None)

        # Cumulative ENDGAME points
        if "endgamePoints" in red and "endgamePoints" in blue:
            tiebreakers.append((red["endgamePoints"], blue["endgamePoints"]))
        else:
            tiebreakers.append(None)

        # Cumulative TELEOP POWER CELL and CONTROL PANEL points
        if (
            "teleopCellPoints" in red
            and "teleopCellPoints" in blue
            and "controlPanelPoints" in red
            and "controlPanelPoints" in blue
        ):
            tiebreakers.append(
                (
                    red["teleopCellPoints"] + red["controlPanelPoints"],
                    blue["teleopCellPoints"] + blue["controlPanelPoints"],
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

        qual_insights = self._calculate_event_insights_2020_helper(qual_matches)
        playoff_insights = self._calculate_event_insights_2020_helper(playoff_matches)

        return {
            "qual": qual_insights,
            "playoff": playoff_insights,
        }

    def _calculate_event_insights_2020_helper(
        self, matches: List[Match]
    ) -> Optional[Dict[str, Any]]:
        # Auto
        init_line_auto = 0
        cell_count_bottom_auto = 0
        cell_count_outer_auto = 0
        cell_count_inner_auto = 0
        cell_points_auto = 0
        points_auto = 0

        # Teleop
        climb_park_teleop = 0
        robots_hanging = 0
        cell_count_bottom_teleop = 0
        cell_count_outer_teleop = 0
        cell_count_inner_teleop = 0
        cell_points_teleop = 0
        control_panel_points = 0
        points_teleop = 0

        # Overall
        exit_init_line_count = 0
        achieve_stage1_count = 0
        achieve_stage2_count = 0
        achieve_stage3_count = 0
        park_count = 0
        hang_count = 0
        generator_level_count = 0
        generator_operational_count = 0
        generator_energized_count = 0

        unicorn_matches = 0
        winning_scores = 0
        win_margins = 0
        total_scores = 0
        total_cell = 0
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

                    # Auto
                    init_line_auto += alliance_breakdown["autoInitLinePoints"]
                    cell_count_bottom_auto += alliance_breakdown["autoCellsBottom"]
                    cell_count_outer_auto += alliance_breakdown["autoCellsOuter"]
                    cell_count_inner_auto += alliance_breakdown["autoCellsInner"]
                    cell_points_auto += alliance_breakdown["autoCellPoints"]
                    points_auto += alliance_breakdown["autoPoints"]

                    # Teleop
                    climb_park_teleop += alliance_breakdown["endgamePoints"]
                    robots_hanging += alliance_breakdown["tba_numRobotsHanging"]
                    cell_count_bottom_teleop += alliance_breakdown["teleopCellsBottom"]
                    cell_count_outer_teleop += alliance_breakdown["teleopCellsOuter"]
                    cell_count_inner_teleop += alliance_breakdown["teleopCellsInner"]
                    cell_points_teleop += alliance_breakdown["teleopCellPoints"]
                    control_panel_points += alliance_breakdown["controlPanelPoints"]
                    points_teleop += alliance_breakdown["teleopPoints"]

                    # Overall
                    for i in range(3):
                        init_line = "initLineRobot{}".format(i + 1)
                        if alliance_breakdown[init_line] == "Exited":
                            exit_init_line_count += 1

                        endgame = "endgameRobot{}".format(i + 1)
                        if alliance_breakdown[endgame] == "Park":
                            park_count += 1
                        elif alliance_breakdown[endgame] == "Hang":
                            hang_count += 1

                    achieve_stage1_count += (
                        1 if alliance_breakdown["stage1Activated"] else 0
                    )
                    achieve_stage2_count += (
                        1 if alliance_breakdown["stage2Activated"] else 0
                    )
                    achieve_stage3_count += (
                        1 if alliance_breakdown["stage3Activated"] else 0
                    )
                    generator_level_count += (
                        1
                        if alliance_breakdown["endgameRungIsLevel"] == "IsLevel"
                        and alliance_breakdown["tba_numRobotsHanging"] > 0
                        else 0
                    )
                    generator_operational_count += (
                        1 if alliance_breakdown["shieldOperationalRankingPoint"] else 0
                    )
                    generator_energized_count += (
                        1 if alliance_breakdown["shieldEnergizedRankingPoint"] else 0
                    )
                    total_cell += (
                        alliance_breakdown["autoCellPoints"]
                        + alliance_breakdown["teleopCellPoints"]
                    )

                    alliance_win = alliance_color == match.winning_alliance
                    unicorn_matches += (
                        1
                        if alliance_win
                        and alliance_breakdown["shieldOperationalRankingPoint"]
                        and alliance_breakdown["shieldEnergizedRankingPoint"]
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
            "average_init_line_points_auto": float(init_line_auto) / opportunities_1x,
            "average_cell_count_bottom_auto": float(cell_count_bottom_auto)
            / opportunities_1x,
            "average_cell_count_outer_auto": float(cell_count_outer_auto)
            / opportunities_1x,
            "average_cell_count_inner_auto": float(cell_count_inner_auto)
            / opportunities_1x,
            "average_cell_count_auto": float(
                cell_count_bottom_auto + cell_count_outer_auto + cell_count_inner_auto
            )
            / opportunities_1x,
            "average_cell_points_auto": float(cell_points_auto) / opportunities_1x,
            "average_points_auto": float(points_auto) / opportunities_1x,
            # Teleop
            "average_endgame_points": float(climb_park_teleop) / opportunities_1x,
            "average_num_robots_hanging": float(robots_hanging) / opportunities_1x,
            "average_cell_count_bottom_teleop": float(cell_count_bottom_teleop)
            / opportunities_1x,
            "average_cell_count_outer_teleop": float(cell_count_outer_teleop)
            / opportunities_1x,
            "average_cell_count_inner_teleop": float(cell_count_inner_teleop)
            / opportunities_1x,
            "average_cell_count_teleop": float(
                cell_count_bottom_teleop
                + cell_count_outer_teleop
                + cell_count_inner_teleop
            )
            / opportunities_1x,
            "average_cell_points_teleop": float(cell_points_teleop) / opportunities_1x,
            "average_control_panel_points": float(control_panel_points)
            / opportunities_1x,
            "average_points_teleop": float(points_teleop) / opportunities_1x,
            # Overall
            "exit_init_line_count": [
                exit_init_line_count,
                opportunities_3x,
                100.0 * float(exit_init_line_count) / opportunities_3x,
            ],
            "achieve_stage1_count": [
                achieve_stage1_count,
                opportunities_1x,
                100.0 * float(achieve_stage1_count) / opportunities_1x,
            ],
            "achieve_stage2_count": [
                achieve_stage2_count,
                opportunities_1x,
                100.0 * float(achieve_stage2_count) / opportunities_1x,
            ],
            "achieve_stage3_count": [
                achieve_stage3_count,
                opportunities_1x,
                100.0 * float(achieve_stage3_count) / opportunities_1x,
            ],
            "park_count": [
                park_count,
                opportunities_3x,
                100.0 * float(park_count) / opportunities_3x,
            ],
            "hang_count": [
                hang_count,
                opportunities_3x,
                100.0 * float(hang_count) / opportunities_3x,
            ],
            "generator_level_count": [
                generator_level_count,
                opportunities_1x,
                100.0 * float(generator_level_count) / opportunities_1x,
            ],
            "generator_operational_rp_achieved": [
                generator_operational_count,
                opportunities_1x,
                100.0 * float(generator_operational_count) / opportunities_1x,
            ],
            "generator_energized_rp_achieved": [
                generator_energized_count,
                opportunities_1x,
                100.0 * float(generator_energized_count) / opportunities_1x,
            ],
            "unicorn_matches": [
                unicorn_matches,
                opportunities_1x,
                100.0 * float(unicorn_matches) / opportunities_1x,
            ],
            "average_win_score": float(winning_scores) / finished_matches,
            "average_win_margin": float(win_margins) / finished_matches,
            "average_score": float(total_scores) / opportunities_1x,
            "average_cell_count_bottom": float(
                cell_count_bottom_auto + cell_count_bottom_teleop
            )
            / opportunities_1x,
            "average_cell_count_outer": float(
                cell_count_outer_auto + cell_count_outer_teleop
            )
            / opportunities_1x,
            "average_cell_count_inner": float(
                cell_count_inner_auto + cell_count_inner_teleop
            )
            / opportunities_1x,
            "average_cell_count": float(
                cell_count_bottom_auto
                + cell_count_outer_auto
                + cell_count_inner_auto
                + cell_count_bottom_teleop
                + cell_count_outer_teleop
                + cell_count_inner_teleop
            )
            / opportunities_1x,
            "average_cell_score": float(total_cell) / opportunities_1x,
            "average_foul_score": float(foul_scores) / opportunities_1x,
            "high_score": list(high_score),
        }
        return event_insights

    def get_prediction_relevant_stats(self) -> List[PredictionStatConfig]:
        return [
            PredictionStatConfig("score", 0, 50**2),
            PredictionStatConfig("power_cells_scored", 0, 20**2),
            PredictionStatConfig("endgame_points", 0, 20**2),
        ]

    def ranking_sort_order_info(self) -> Optional[List[RankingSortOrderInfo]]:
        return [
            {"name": "Ranking Score", "precision": 2},
            {"name": "Auto", "precision": 0},
            {"name": "End Game", "precision": 0},
            {"name": "Teleop Cell + CPanel", "precision": 0},
        ]

    def round_robin_tiebreak_keys(self) -> List[str]:
        return []

    def round_robin_tiebreaker_names(self) -> List[str]:
        return []
