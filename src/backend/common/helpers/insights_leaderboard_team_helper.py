from collections import defaultdict
from typing import List, Optional

from backend.common.consts.award_type import AwardType, BLUE_BANNER_AWARDS
from backend.common.consts.event_type import NON_CMP_EVENT_TYPES
from backend.common.helpers.insights_helper_utils import (
    LeaderboardInsightArguments,
    make_insights_from_functions,
    make_leaderboard_from_dict_counts,
)
from backend.common.models.insight import Insight


class InsightsLeaderboardTeamHelper:
    @staticmethod
    def make_insights(year: int) -> List[Insight]:
        return make_insights_from_functions(
            year,
            [
                InsightsLeaderboardTeamHelper._most_blue_banners,
                InsightsLeaderboardTeamHelper._most_awards,
                InsightsLeaderboardTeamHelper._most_non_champs_event_wins,
                InsightsLeaderboardTeamHelper._most_matches_played,
                InsightsLeaderboardTeamHelper._most_events_played_at,
                InsightsLeaderboardTeamHelper._most_unique_teams_played_with_or_against,
            ],
        )

    @staticmethod
    def _most_blue_banners(arguments: LeaderboardInsightArguments) -> Optional[Insight]:
        count = defaultdict(int)

        for award in arguments.awards:
            if award.award_type_enum in BLUE_BANNER_AWARDS and award.count_banner:
                for team_key in award.team_list:
                    count[team_key.id()] += 1

        return make_leaderboard_from_dict_counts(
            count, Insight.TYPED_LEADERBOARD_BLUE_BANNERS, arguments.year
        )

    @staticmethod
    def _most_awards(arguments: LeaderboardInsightArguments) -> Optional[Insight]:
        count = defaultdict(int)

        for award in arguments.awards:
            if award.award_type_enum == AwardType.WILDCARD:
                continue

            for team_key in award.team_list:
                count[team_key.id()] += 1

        return make_leaderboard_from_dict_counts(
            count, Insight.TYPED_LEADERBOARD_MOST_AWARDS, arguments.year
        )

    @staticmethod
    def _most_non_champs_event_wins(
        arguments: LeaderboardInsightArguments,
    ) -> Optional[Insight]:
        count = defaultdict(int)

        for award in arguments.awards:
            if (
                award.award_type_enum == AwardType.WINNER
                and award.event_type_enum in NON_CMP_EVENT_TYPES
            ):
                for team_key in award.team_list:
                    count[team_key.id()] += 1

        return make_leaderboard_from_dict_counts(
            count, Insight.TYPED_LEADERBOARD_MOST_NON_CHAMPS_EVENT_WINS, arguments.year
        )

    @staticmethod
    def _most_matches_played(
        arguments: LeaderboardInsightArguments,
    ) -> Optional[Insight]:
        count = defaultdict(int)

        for match in arguments.matches:
            if match.has_been_played:
                for team_key in match.team_keys:
                    count[team_key.id()] += 1

        return make_leaderboard_from_dict_counts(
            count, Insight.TYPED_LEADERBOARD_MOST_MATCHES_PLAYED, arguments.year
        )

    @staticmethod
    def _most_events_played_at(
        arguments: LeaderboardInsightArguments,
    ) -> Optional[Insight]:
        played_at = defaultdict(set)

        for match in arguments.matches:
            if match.has_been_played:
                for team_key in match.team_keys:
                    played_at[team_key.id()].add(match.event_key_name)

        counts = {tk: len(events) for tk, events in played_at.items()}
        return make_leaderboard_from_dict_counts(
            counts, Insight.TYPED_LEADERBOARD_MOST_EVENTS_PLAYED_AT, arguments.year
        )

    @staticmethod
    def _most_unique_teams_played_with_or_against(
        arguments: LeaderboardInsightArguments,
    ) -> Optional[Insight]:
        seen_teams = defaultdict(set)

        for match in arguments.matches:
            if match.has_been_played:
                for a in match.team_key_names:
                    for b in match.team_key_names:
                        if a != b:
                            seen_teams[a].add(b)

        counts = {tk: len(teams) for tk, teams in seen_teams.items()}
        return make_leaderboard_from_dict_counts(
            counts,
            Insight.TYPED_LEADERBOARD_MOST_UNIQUE_TEAMS_PLAYED_WITH_AGAINST,
            arguments.year,
        )
