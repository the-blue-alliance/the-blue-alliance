from collections import defaultdict
from statistics import median
from typing import List, Optional

from pyre_extensions import none_throws

from backend.common.consts.alliance_color import AllianceColor
from backend.common.helpers.insights_helper_utils import (
    LeaderboardInsightArguments,
    make_insights_from_functions,
    make_leaderboard_from_dict_counts,
)
from backend.common.models.insight import Insight


class InsightsLeaderboardEventHelper:
    @staticmethod
    def make_insights(year: int) -> List[Insight]:
        return make_insights_from_functions(
            year,
            [
                InsightsLeaderboardEventHelper._highest_median_score,
            ],
        )

    @staticmethod
    def _highest_median_score(
        arguments: LeaderboardInsightArguments,
    ) -> Optional[Insight]:
        clean_scores = defaultdict(list)

        for match in arguments.matches():
            if match.has_been_played:
                redScore = int(match.alliances[AllianceColor.RED]["score"])
                blueScore = int(match.alliances[AllianceColor.BLUE]["score"])

                if match.year >= 2016:
                    if match.score_breakdown:
                        redScore -= none_throws(match.score_breakdown)[
                            AllianceColor.RED
                        ].get("foulPoints", 0)
                        blueScore -= none_throws(match.score_breakdown)[
                            AllianceColor.BLUE
                        ].get("foulPoints", 0)

                clean_scores[match.event.id()].append(redScore)
                clean_scores[match.event.id()].append(blueScore)

        medians = defaultdict(int)
        for event_key, scores_list in clean_scores.items():
            if len(scores_list) < 10:
                continue

            medians[event_key] = median(sorted(scores_list))

        return make_leaderboard_from_dict_counts(
            medians,
            Insight.TYPED_LEADERBOARD_HIGHEST_MEDIAN_SCORE_BY_EVENT,
            arguments.year,
        )
