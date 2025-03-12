from collections import defaultdict
from typing import List, Optional

from pyre_extensions import none_throws

from backend.common.consts.alliance_color import AllianceColor
from backend.common.helpers.insights_helper_utils import (
    LeaderboardInsightArguments,
    make_insights_from_functions,
    make_leaderboard_from_dict_counts,
)
from backend.common.models.insight import Insight


class InsightsLeaderboardMatchHelper:
    @staticmethod
    def make_insights(year: int) -> List[Insight]:
        return make_insights_from_functions(
            year,
            [
                InsightsLeaderboardMatchHelper._highest_match_clean_score,
                InsightsLeaderboardMatchHelper._highest_match_clean_combined_score,
                InsightsLeaderboardMatchHelper._2025_most_coral_scored,
            ],
        )

    @staticmethod
    def _highest_match_clean_score(
        arguments: LeaderboardInsightArguments,
    ) -> Optional[Insight]:
        clean_scores = defaultdict(int)

        for match in arguments.matches():
            if match.has_been_played:
                redScore = int(match.alliances[AllianceColor.RED]["score"])
                blueScore = int(match.alliances[AllianceColor.BLUE]["score"])

                if match.year >= 2016 and match.score_breakdown is not None:
                    redScore -= none_throws(match.score_breakdown)[
                        AllianceColor.RED
                    ].get("foulPoints", 0)
                    blueScore -= none_throws(match.score_breakdown)[
                        AllianceColor.BLUE
                    ].get("foulPoints", 0)

                clean_scores[match.key.id()] = max(redScore, blueScore)

        return make_leaderboard_from_dict_counts(
            clean_scores,
            Insight.TYPED_LEADERBOARD_HIGHEST_MATCH_CLEAN_SCORE,
            arguments.year,
        )

    @staticmethod
    def _highest_match_clean_combined_score(
        arguments: LeaderboardInsightArguments,
    ) -> Optional[Insight]:
        clean_scores = defaultdict(int)

        for match in arguments.matches():
            if match.has_been_played:
                redScore = int(match.alliances[AllianceColor.RED]["score"])
                blueScore = int(match.alliances[AllianceColor.BLUE]["score"])

                if match.year >= 2016 and match.score_breakdown is not None:
                    redScore -= none_throws(match.score_breakdown)[
                        AllianceColor.RED
                    ].get("foulPoints", 0)
                    blueScore -= none_throws(match.score_breakdown)[
                        AllianceColor.BLUE
                    ].get("foulPoints", 0)

                clean_scores[match.key.id()] = redScore + blueScore

        return make_leaderboard_from_dict_counts(
            clean_scores,
            Insight.TYPED_LEADERBOARD_HIGHEST_MATCH_CLEAN_COMBINED_SCORE,
            arguments.year,
        )

    @staticmethod
    def _2025_most_coral_scored(
        arguments: LeaderboardInsightArguments,
    ) -> Optional[Insight]:
        if arguments.year != 2025:
            return None

        coral_scores = defaultdict(int)

        for match in arguments.matches():
            if match.has_been_played and match.score_breakdown is not None:
                red_coral = (
                    none_throws(match.score_breakdown)[AllianceColor.RED][
                        "teleopCoralCount"
                    ]
                    + none_throws(match.score_breakdown)[AllianceColor.RED][
                        "autoCoralCount"
                    ]
                )
                blue_coral = (
                    none_throws(match.score_breakdown)[AllianceColor.BLUE][
                        "teleopCoralCount"
                    ]
                    + none_throws(match.score_breakdown)[AllianceColor.BLUE][
                        "autoCoralCount"
                    ]
                )

                coral_scores[match.key.id()] = max(red_coral, blue_coral)

        return make_leaderboard_from_dict_counts(
            coral_scores,
            Insight.TYPED_LEADERBOARD_2025_MOST_CORAL_SCORED,
            arguments.year,
        )
