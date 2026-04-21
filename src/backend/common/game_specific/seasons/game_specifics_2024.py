from __future__ import annotations

from typing import Any, Dict, List, Optional, Set, Tuple

from pyre_extensions import none_throws

from backend.common.consts.alliance_color import AllianceColor
from backend.common.consts.comp_level import CompLevel
from backend.common.game_specific.base import SeasonGameConfig, StatAccessor, TCriteria
from backend.common.models.event_insights import EventInsights
from backend.common.models.match import Match
from backend.common.models.ranking_sort_order_info import RankingSortOrderInfo


class GameSpecifics2024(SeasonGameConfig):
    def tiebreak_criteria(self, red: Dict, blue: Dict) -> List[TCriteria]:
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

        # ALLIANCE STAGE points
        if "endGameTotalStagePoints" in red and "endGameTotalStagePoints" in blue:
            tiebreakers.append(
                (
                    red["endGameTotalStagePoints"],
                    blue["endGameTotalStagePoints"],
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

        qual_insights = self._calculate_event_insights_2024_helper(qual_matches)
        playoff_insights = self._calculate_event_insights_2024_helper(playoff_matches)

        return {
            "qual": qual_insights,
            "playoff": playoff_insights,
        }

    def _calculate_event_insights_2024_helper(
        self, matches: List[Match]
    ) -> Optional[Dict[str, Any]]:
        melody_rp_count = 0
        ensemble_rp_count = 0
        coopertition_count = 0
        four_rp_count = 0
        six_rp_count = 0

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

            if red_sb.get("melodyBonusAchieved", False):
                melody_rp_count += 1
            if blue_sb.get("melodyBonusAchieved", False):
                melody_rp_count += 1

            if red_sb.get("ensembleBonusAchieved", False):
                ensemble_rp_count += 1
            if blue_sb.get("ensembleBonusAchieved", False):
                ensemble_rp_count += 1

            if red_sb.get("coopertitionCriteriaMet", False):
                coopertition_count += 1
            if blue_sb.get("coopertitionCriteriaMet", False):
                coopertition_count += 1

            red_all_rp = red_sb.get("melodyBonusAchieved", False) and red_sb.get(
                "melodyBonusAchieved", False
            )
            blue_all_rp = blue_sb.get("melodyBonusAchieved", False) and blue_sb.get(
                "melodyBonusAchieved", False
            )

            if (red_score > blue_score and red_all_rp) or (
                blue_score > red_score and blue_all_rp
            ):
                four_rp_count += 1
                if red_all_rp and blue_all_rp:
                    six_rp_count += 1

            total_scores += red_score + blue_score
            total_win_margins += win_score - min(red_score, blue_score)
            total_winning_scores += win_score

        if finished_matches == 0:
            return None

        return {
            "melody_rp_count": [
                melody_rp_count,
                finished_matches * 2,
                100.0 * melody_rp_count / (finished_matches * 2),
            ],
            "ensemble_rp_count": [
                ensemble_rp_count,
                finished_matches * 2,
                100.0 * ensemble_rp_count / (finished_matches * 2),
            ],
            "coopertition_count": [
                coopertition_count,
                finished_matches * 2,
                100.0 * coopertition_count / (finished_matches * 2),
            ],
            "four_rp_count": [
                four_rp_count,
                finished_matches,
                100.0 * four_rp_count / finished_matches,
            ],
            "six_rp_count": [
                six_rp_count,
                finished_matches,
                100.0 * six_rp_count / finished_matches,
            ],
            "average_score": total_scores / (finished_matches * 2),
            "average_win_margin": total_win_margins / finished_matches,
            "average_winning_score": total_winning_scores / finished_matches,
            "high_score": high_score,
        }

    def get_manual_coprs(self) -> Dict[str, StatAccessor]:
        return {
            "Total Mic": lambda match, color: sum(
                [
                    match.score_breakdown[color].get("micCenterStage", 0),
                    match.score_breakdown[color].get("micStageLeft", 0),
                    match.score_breakdown[color].get("micStageRight", 0),
                ]
            ),
            "Total Trap": lambda match, color: sum(
                [
                    match.score_breakdown[color].get("trapCenterStage", 0),
                    match.score_breakdown[color].get("trapStageLeft", 0),
                    match.score_breakdown[color].get("trapStageRight", 0),
                ]
            ),
            "Total Teleop Game Pieces": lambda match, color: sum(
                [
                    match.score_breakdown[color].get("teleopAmpNoteCount", 0),
                    match.score_breakdown[color].get("teleopSpeakerNoteCount", 0),
                    match.score_breakdown[color].get(
                        "teleopSpeakerNoteAmplifiedCount", 0
                    ),
                ]
            ),
            "Total Auto Game Pieces": lambda match, color: sum(
                [
                    match.score_breakdown[color].get("autoAmpNoteCount", 0),
                    match.score_breakdown[color].get("autoSpeakerNoteCount", 0),
                ]
            ),
            "Total Overall Game Pieces": lambda match, color: sum(
                [
                    match.score_breakdown[color].get("autoAmpNoteCount", 0),
                    match.score_breakdown[color].get("autoSpeakerNoteCount", 0),
                    match.score_breakdown[color].get("teleopAmpNoteCount", 0),
                    match.score_breakdown[color].get("teleopSpeakerNoteCount", 0),
                    match.score_breakdown[color].get(
                        "teleopSpeakerNoteAmplifiedCount", 0
                    ),
                ]
            ),
            "Amplification Rate": lambda match, color: match.score_breakdown[color].get(
                "teleopSpeakerNoteAmplifiedCount", 0
            )
            / max(
                1,
                match.score_breakdown[color].get("teleopSpeakerNoteCount", 0)
                + match.score_breakdown[color].get(
                    "teleopSpeakerNoteAmplifiedCount", 0
                ),
            ),
        }

    def get_prediction_relevant_stats(self) -> List[Tuple[str, int, int]]:
        return [
            ("score", 0, 20**2),
            ("note_scored", 0, 10**2),
            ("stage_points", 0, 10**2),
        ]

    def ranking_bonus_rp_breakdown_fields(self) -> List[str]:
        return ["melodyBonusAchieved", "ensembleBonusAchieved"]

    def ranking_bonus_rp_prediction_fields(self) -> List[str]:
        return ["prob_melody_bonus", "prob_ensemble_bonus"]

    def ranking_tiebreaker_breakdown_field(self) -> Optional[str]:
        return "totalPoints"

    def ranking_tiebreaker_prediction_field(self) -> Optional[str]:
        return "score"

    def ranking_sort_order_info(self) -> Optional[List[RankingSortOrderInfo]]:
        return [
            {"name": "Ranking Score", "precision": 2},
            {"name": "Avg Coop", "precision": 2},
            {"name": "Avg Match", "precision": 2},
            {"name": "Avg Auto", "precision": 2},
            {"name": "Avg Stage", "precision": 2},
        ]

    def valid_score_breakdown_keys(self) -> Set[str]:
        return set(
            [
                "adjustPoints",
                "autoAmpNoteCount",
                "autoAmpNotePoints",
                "autoLeavePoints",
                "autoLineRobot1",
                "autoLineRobot2",
                "autoLineRobot3",
                "autoPoints",
                "autoSpeakerNoteCount",
                "autoSpeakerNotePoints",
                "autoTotalNotePoints",
                "coopertitionBonusAchieved",
                "coopertitionCriteriaMet",
                "coopNotePlayed",
                "endGameHarmonyPoints",
                "endGameNoteInTrapPoints",
                "endGameOnStagePoints",
                "endGameParkPoints",
                "endGameRobot1",
                "endGameRobot2",
                "endGameRobot3",
                "endGameSpotLightBonusPoints",
                "endGameTotalStagePoints",
                "ensembleBonusAchieved",
                "ensembleBonusOnStageRobotsThreshold",
                "ensembleBonusStagePointsThreshold",
                "foulCount",
                "foulPoints",
                "g206Penalty",
                "g408Penalty",
                "g424Penalty",
                "melodyBonusAchieved",
                "melodyBonusThreshold",
                "melodyBonusThresholdCoop",
                "melodyBonusThresholdNonCoop",
                "micCenterStage",
                "micStageLeft",
                "micStageRight",
                "rp",
                "techFoulCount",
                "teleopAmpNoteCount",
                "teleopAmpNotePoints",
                "teleopPoints",
                "teleopSpeakerNoteAmplifiedCount",
                "teleopSpeakerNoteAmplifiedPoints",
                "teleopSpeakerNoteCount",
                "teleopSpeakerNotePoints",
                "teleopTotalNotePoints",
                "totalPoints",
                "trapCenterStage",
                "trapStageLeft",
                "trapStageRight",
                # fields added by TBA:
                "tba_extraRp1",
                "tba_extraRp2",
            ]
        )
