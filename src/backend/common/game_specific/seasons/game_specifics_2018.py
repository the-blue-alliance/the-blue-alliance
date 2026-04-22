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
from backend.common.frc_api.types import ScoreDetailModelAlliance2018
from backend.common.game_specific.base import (
    PredictionStatConfig,
    TCriteria,
    TotalPointsScoreBonusRpGameConfig,
)
from backend.common.models.event_insights import EventInsights
from backend.common.models.match import Match
from backend.common.models.ranking_sort_order_info import RankingSortOrderInfo


class GameSpecifics2018(
    TotalPointsScoreBonusRpGameConfig[ScoreDetailModelAlliance2018]
):
    SCORE_BREAKDOWN_MODEL = ScoreDetailModelAlliance2018
    BONUS_RP_BREAKDOWN_FIELDS = ("autoQuestRankingPoint", "faceTheBossRankingPoint")
    BONUS_RP_PREDICTION_FIELDS = ("prob_auto_quest", "prob_face_boss")
    EXTRA_SCORE_BREAKDOWN_KEYS = frozenset(["tba_gameData"])

    def tiebreak_criteria(
        self,
        red: ScoreDetailModelAlliance2018,
        blue: ScoreDetailModelAlliance2018,
    ) -> List[TCriteria]:
        return []

    def calculate_event_insights(self, matches: List[Match]) -> Optional[EventInsights]:
        qual_matches = []
        playoff_matches = []
        for match in matches:
            if match.comp_level == CompLevel.QM:
                qual_matches.append(match)
            else:
                playoff_matches.append(match)

        qual_insights = self._calculate_event_insights_2018_helper(qual_matches)
        playoff_insights = self._calculate_event_insights_2018_helper(playoff_matches)

        return {
            "qual": qual_insights,
            "playoff": playoff_insights,
        }

    def _calculate_event_insights_2018_helper(
        self, matches: List[Match]
    ) -> Optional[Dict[str, Any]]:
        # Auto
        run_points_auto = 0
        scale_ownership_time_auto = 0
        switch_ownership_time_auto = 0
        points_auto = 0

        run_counts_auto = 0
        switch_owned_counts_auto = 0

        # Teleop
        scale_ownership_time_teleop = 0
        switch_ownership_time_teleop = 0
        points_teleop = 0

        # Overall
        winning_scale_ownership_percentage_auto = 0
        winning_own_switch_ownership_percentage_auto = 0
        winning_scale_ownership_percentage_teleop = 0
        winning_own_switch_ownership_percentage_teleop = 0
        winning_opp_switch_denial_percentage_teleop = 0
        winning_scale_ownership_percentage = 0
        winning_own_switch_ownership_percentage = 0

        scale_neutral_percentage_auto = 0
        scale_neutral_percentage_teleop = 0
        scale_neutral_percentage = 0

        force_played = 0
        levitate_played = 0
        boost_played = 0
        force_played_counts = 0
        levitate_played_counts = 0
        boost_played_counts = 0
        vault_points = 0
        endgame_points = 0

        climb_counts = 0
        auto_quest_achieved = 0
        face_the_boss_achieved = 0
        unicorn_matches = 0

        winning_scores = 0
        win_margins = 0
        total_scores = 0
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
                    opp_alliance_breakdown = score_breakdown[OPPONENT[alliance_color]]
                    alliance_win = alliance_color == match.winning_alliance

                    # Auto
                    run_points_auto += alliance_breakdown["autoRunPoints"]
                    scale_ownership_time_auto += alliance_breakdown[
                        "autoScaleOwnershipSec"
                    ]
                    switch_ownership_time_auto += alliance_breakdown[
                        "autoSwitchOwnershipSec"
                    ]
                    points_auto += alliance_breakdown["autoPoints"]

                    switch_owned_counts_auto += (
                        1 if alliance_breakdown["autoSwitchAtZero"] else 0
                    )
                    alliance_run_counts_auto = 0
                    for i in range(3):
                        alliance_run_counts_auto += (
                            1
                            if alliance_breakdown["autoRobot{}".format(i + 1)]
                            == "AutoRun"
                            else 0
                        )
                    run_counts_auto += alliance_run_counts_auto

                    # Teleop
                    scale_ownership_time_teleop += alliance_breakdown[
                        "teleopScaleOwnershipSec"
                    ]
                    switch_ownership_time_teleop += alliance_breakdown[
                        "teleopSwitchOwnershipSec"
                    ]
                    points_teleop += alliance_breakdown["teleopPoints"]

                    # Overall
                    if alliance_win:
                        winning_scale_ownership_percentage_auto += (
                            float(alliance_breakdown["autoScaleOwnershipSec"]) / 15
                        )
                        winning_own_switch_ownership_percentage_auto += (
                            float(alliance_breakdown["autoSwitchOwnershipSec"]) / 15
                        )

                        winning_scale_ownership_percentage_teleop += (
                            float(alliance_breakdown["teleopScaleOwnershipSec"]) / 135
                        )
                        winning_own_switch_ownership_percentage_teleop += (
                            float(alliance_breakdown["teleopSwitchOwnershipSec"]) / 135
                        )
                        winning_opp_switch_denial_percentage_teleop += (
                            float(
                                135 - opp_alliance_breakdown["teleopSwitchOwnershipSec"]
                            )
                            / 135
                        )

                        winning_scale_ownership_percentage += (
                            float(
                                alliance_breakdown["autoScaleOwnershipSec"]
                                + alliance_breakdown["teleopScaleOwnershipSec"]
                            )
                            / 150
                        )
                        winning_own_switch_ownership_percentage += (
                            float(
                                alliance_breakdown["autoSwitchOwnershipSec"]
                                + alliance_breakdown["teleopSwitchOwnershipSec"]
                            )
                            / 150
                        )

                    scale_neutral_percentage_auto += (
                        float(7.5 - alliance_breakdown["autoScaleOwnershipSec"]) / 7.5
                    )
                    scale_neutral_percentage_teleop += (
                        float(67.5 - alliance_breakdown["teleopScaleOwnershipSec"])
                        / 67.5
                    )
                    scale_neutral_percentage += (
                        float(
                            75
                            - alliance_breakdown["autoScaleOwnershipSec"]
                            - alliance_breakdown["teleopScaleOwnershipSec"]
                        )
                        / 75
                    )

                    force_played += alliance_breakdown["vaultForcePlayed"]
                    levitate_played += alliance_breakdown["vaultLevitatePlayed"]
                    boost_played += alliance_breakdown["vaultBoostPlayed"]
                    force_played_counts += alliance_breakdown["vaultForcePlayed"] > 0
                    levitate_played_counts += (
                        alliance_breakdown["vaultLevitatePlayed"] > 0
                    )
                    boost_played_counts += alliance_breakdown["vaultBoostPlayed"] > 0

                    vault_points += alliance_breakdown["vaultPoints"]
                    endgame_points += alliance_breakdown["endgamePoints"]

                    alliance_climb_levitate_counts = 0
                    for i in range(3):
                        alliance_climb_levitate_counts += (
                            1
                            if alliance_breakdown["endgameRobot{}".format(i + 1)]
                            in {"Climbing", "Levitate"}
                            else 0
                        )
                        climb_counts += (
                            1
                            if alliance_breakdown["endgameRobot{}".format(i + 1)]
                            == "Climbing"
                            else 0
                        )

                    alliance_auto_quest_achieved = (
                        alliance_run_counts_auto == 3
                        and alliance_breakdown["autoSwitchAtZero"]
                    )
                    alliance_face_the_boss_achieved = (
                        alliance_climb_levitate_counts == 3
                    )
                    auto_quest_achieved += 1 if alliance_auto_quest_achieved else 0
                    face_the_boss_achieved += (
                        1 if alliance_face_the_boss_achieved else 0
                    )
                    unicorn_matches += (
                        1
                        if (
                            alliance_win
                            and alliance_auto_quest_achieved
                            and alliance_face_the_boss_achieved
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
        event_insights = {
            # Auto
            "average_run_points_auto": float(run_points_auto) / (2 * finished_matches),
            "average_scale_ownership_points_auto": float(scale_ownership_time_auto * 2)
            / (2 * finished_matches),
            "average_switch_ownership_points_auto": float(
                switch_ownership_time_auto * 2
            )
            / (2 * finished_matches),
            "average_points_auto": float(points_auto) / (2 * finished_matches),
            "run_counts_auto": [
                run_counts_auto,
                opportunities_3x,
                100.0 * float(run_counts_auto) / opportunities_3x,
            ],
            "switch_owned_counts_auto": [
                switch_owned_counts_auto,
                opportunities_1x,
                100.0 * float(switch_owned_counts_auto) / opportunities_1x,
            ],
            # Teleop
            "average_scale_ownership_points_teleop": float(scale_ownership_time_teleop)
            / (2 * finished_matches),
            "average_switch_ownership_points_teleop": float(
                switch_ownership_time_teleop
            )
            / (2 * finished_matches),
            "average_points_teleop": float(points_teleop) / (2 * finished_matches),
            # Overall
            "climb_counts": [
                climb_counts,
                opportunities_3x,
                100.0 * float(climb_counts) / opportunities_3x,
            ],
            "force_played_counts": [
                force_played_counts,
                opportunities_1x,
                100.0 * float(force_played_counts) / opportunities_1x,
            ],
            "levitate_played_counts": [
                levitate_played_counts,
                opportunities_1x,
                100.0 * float(levitate_played_counts) / opportunities_1x,
            ],
            "boost_played_counts": [
                boost_played_counts,
                opportunities_1x,
                100.0 * float(boost_played_counts) / opportunities_1x,
            ],
            "average_scale_ownership_points": float(
                scale_ownership_time_auto * 2 + scale_ownership_time_teleop
            )
            / (2 * finished_matches),
            "average_switch_ownership_points": float(
                switch_ownership_time_auto * 2 + switch_ownership_time_teleop
            )
            / (2 * finished_matches),
            "winning_scale_ownership_percentage_auto": 100.0
            * float(winning_scale_ownership_percentage_auto)
            / finished_matches,
            "winning_own_switch_ownership_percentage_auto": 100.0
            * float(winning_own_switch_ownership_percentage_auto)
            / finished_matches,
            "winning_scale_ownership_percentage_teleop": 100.0
            * float(winning_scale_ownership_percentage_teleop)
            / finished_matches,
            "winning_own_switch_ownership_percentage_teleop": 100.0
            * float(winning_own_switch_ownership_percentage_teleop)
            / finished_matches,
            "winning_opp_switch_denial_percentage_teleop": 100.0
            * float(winning_opp_switch_denial_percentage_teleop)
            / finished_matches,
            "winning_scale_ownership_percentage": 100.0
            * float(winning_scale_ownership_percentage)
            / finished_matches,
            "winning_own_switch_ownership_percentage": 100.0
            * float(winning_own_switch_ownership_percentage)
            / finished_matches,
            "scale_neutral_percentage_auto": 100.0
            * float(scale_neutral_percentage_auto)
            / (2 * finished_matches),
            "scale_neutral_percentage_teleop": 100.0
            * float(scale_neutral_percentage_teleop)
            / (2 * finished_matches),
            "scale_neutral_percentage": 100.0
            * float(scale_neutral_percentage)
            / (2 * finished_matches),
            "average_force_played": float(force_played) / force_played_counts,
            "average_boost_played": float(boost_played) / boost_played_counts,
            "average_vault_points": float(vault_points) / (2 * finished_matches),
            "average_endgame_points": float(endgame_points) / (2 * finished_matches),
            "average_win_score": float(winning_scores) / finished_matches,
            "average_win_margin": float(win_margins) / finished_matches,
            "average_score": float(total_scores) / (2 * finished_matches),
            "average_foul_score": float(foul_scores) / (2 * finished_matches),
            "high_score": list(high_score),  # [score, match key, match name]
            "auto_quest_achieved": [
                auto_quest_achieved,
                opportunities_1x,
                100.0 * float(auto_quest_achieved) / opportunities_1x,
            ],
            "face_the_boss_achieved": [
                face_the_boss_achieved,
                opportunities_1x,
                100.0 * float(face_the_boss_achieved) / opportunities_1x,
            ],
            "unicorn_matches": [
                unicorn_matches,
                opportunities_1x,
                100.0 * float(unicorn_matches) / opportunities_1x,
            ],
        }

        return event_insights

    def get_prediction_relevant_stats(self) -> List[PredictionStatConfig]:
        return [
            PredictionStatConfig("score", 50, 30**2),
            PredictionStatConfig("auto_points", 0, 1**2),
            PredictionStatConfig("endgame_points", 0, 1**2),
        ]

    def ranking_sort_order_info(self) -> Optional[List[RankingSortOrderInfo]]:
        return [
            {"name": "Ranking Score", "precision": 2},
            {"name": "Park/Climb Points", "precision": 0},
            {"name": "Auto", "precision": 0},
            {"name": "Ownership", "precision": 0},
            {"name": "Vault", "precision": 0},
        ]

    def round_robin_tiebreak_keys(self) -> List[str]:
        return ["endgamePoints", "autoPoints"]

    def round_robin_tiebreaker_names(self) -> List[str]:
        return ["Park/Climb Points", "Auto Points"]
