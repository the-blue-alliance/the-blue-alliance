from abc import ABC
from collections import defaultdict
from typing import List, Optional

from backend.common.consts.award_type import AwardType, BLUE_BANNER_AWARDS
from backend.common.consts.event_type import (
    EventType,
    NON_CMP_EVENT_TYPES,
    SEASON_EVENT_TYPES,
)
from backend.common.helpers.insights_helper_utils import (
    make_leaderboard_from_dict_counts,
)
from backend.common.helpers.season_helper import SeasonHelper
from backend.common.models.event import Event
from backend.common.models.insight import Insight
from backend.common.models.keys import Year
from backend.common.queries.event_query import EventListQuery


class AbstractLeaderboardCalculator(ABC):
    def on_event(self, event: Event) -> None:
        pass

    def make_insight(self, year: Year) -> Optional[Insight]:
        pass


class MostBlueBannersCalculator(AbstractLeaderboardCalculator):
    def __init__(self):
        self.count = defaultdict(int)

    def on_event(self, event: Event) -> None:
        for award in event.awards:
            if award.award_type_enum in BLUE_BANNER_AWARDS and award.count_banner:
                for team_key in award.team_list:
                    self.count[team_key.id()] += 1

    def make_insight(self, year: Year) -> Optional[Insight]:
        return make_leaderboard_from_dict_counts(
            self.count, Insight.TYPED_LEADERBOARD_BLUE_BANNERS, year
        )


class MostAwardsCalculator(AbstractLeaderboardCalculator):
    def __init__(self):
        self.count = defaultdict(int)

    def on_event(self, event: Event) -> None:
        for award in event.awards:
            if award.award_type_enum == AwardType.WILDCARD:
                continue

            for team_key in award.team_list:
                self.count[team_key.id()] += 1

    def make_insight(self, year: Year) -> Optional[Insight]:
        return make_leaderboard_from_dict_counts(
            self.count, Insight.TYPED_LEADERBOARD_MOST_AWARDS, year
        )


class MostNonChampsEventWinsCalculator(AbstractLeaderboardCalculator):
    def __init__(self):
        self.count = defaultdict(int)

    def on_event(self, event: Event) -> None:
        for award in event.awards:
            if (
                award.award_type_enum == AwardType.WINNER
                and award.event_type_enum in NON_CMP_EVENT_TYPES
            ):
                for team_key in award.team_list:
                    self.count[team_key.id()] += 1

    def make_insight(self, year: Year) -> Optional[Insight]:
        return make_leaderboard_from_dict_counts(
            self.count, Insight.TYPED_LEADERBOARD_MOST_NON_CHAMPS_EVENT_WINS, year
        )


class MostMatchesPlayedCalculator(AbstractLeaderboardCalculator):
    def __init__(self):
        self.count = defaultdict(int)

    def on_event(self, event: Event) -> None:
        for match in event.matches:
            if match.has_been_played:
                for team_key in match.team_keys:
                    self.count[team_key.id()] += 1

    def make_insight(self, year: Year) -> Optional[Insight]:
        return make_leaderboard_from_dict_counts(
            self.count, Insight.TYPED_LEADERBOARD_MOST_MATCHES_PLAYED, year
        )


class MostEventsPlayedAtCalculator(AbstractLeaderboardCalculator):
    def __init__(self):
        self.events_played = defaultdict(set)

    def on_event(self, event: Event) -> None:
        for match in event.matches:
            if match.has_been_played:
                for team_key in match.team_keys:
                    self.events_played[team_key.id()].add(event.key_name)

    def make_insight(self, year: Year) -> Optional[Insight]:
        return make_leaderboard_from_dict_counts(
            {tk: len(events) for tk, events in self.events_played.items()},
            Insight.TYPED_LEADERBOARD_MOST_EVENTS_PLAYED_AT,
            year,
        )


class MostUniqueTeamsPlayedWithOrAgainstCalculator(AbstractLeaderboardCalculator):
    def __init__(self):
        self.seen_teams = defaultdict(set)

    def on_event(self, event: Event) -> None:
        for match in event.matches:
            if match.has_been_played:
                for a in match.team_key_names:
                    for b in match.team_key_names:
                        if a != b:
                            self.seen_teams[a].add(b)
                            self.seen_teams[b].add(a)

    def make_insight(self, year: Year) -> Optional[Insight]:
        return make_leaderboard_from_dict_counts(
            {tk: len(teams) for tk, teams in self.seen_teams.items()},
            Insight.TYPED_LEADERBOARD_MOST_UNIQUE_TEAMS_PLAYED_WITH_AGAINST,
            year,
        )


class MostNonChampsImpactWinsCalculator(AbstractLeaderboardCalculator):
    def __init__(self):
        self.count = defaultdict(int)

    def on_event(self, event: Event) -> None:
        for award in event.awards:
            if (
                award.award_type_enum == AwardType.CHAIRMANS
                and award.event_type_enum in NON_CMP_EVENT_TYPES
            ):
                for team_key in award.team_list:
                    self.count[team_key.id()] += 1

    def make_insight(self, year: Year) -> Optional[Insight]:
        if year != 0:
            return None

        return make_leaderboard_from_dict_counts(
            self.count, Insight.TYPED_LEADERBOARD_MOST_NON_CHAMPS_IMPACT_WINS, year
        )


class MostWffasCalculator(AbstractLeaderboardCalculator):
    def __init__(self):
        self.count = defaultdict(int)

    def on_event(self, event: Event) -> None:
        for award in event.awards:
            if (
                award.award_type_enum == AwardType.WOODIE_FLOWERS
                and award.event_type_enum in NON_CMP_EVENT_TYPES
            ):
                for team_key in award.team_list:
                    self.count[team_key.id()] += 1

    def make_insight(self, year: Year) -> Optional[Insight]:
        if year != 0:
            return None

        return make_leaderboard_from_dict_counts(
            self.count, Insight.TYPED_LEADERBOARD_MOST_WFFAS, year
        )


class LongestEinsteinStreakCalculator(AbstractLeaderboardCalculator):
    def __init__(self):
        self.einstein_appearances = defaultdict(list)

    def on_event(self, event: Event) -> None:
        for award in event.awards:
            if (
                award.award_type_enum == AwardType.WINNER
                and award.event_type_enum == EventType.CMP_DIVISION
            ):
                for team_key in award.team_list:
                    self.einstein_appearances[team_key.id()].append(event.year)

    @staticmethod
    def are_years_consecutive(a: Year, b: Year) -> bool:
        # 2020, 2021 divisions didn't happen because COVID
        if a in [2019, 2022] and b in [2019, 2022] and a != b:
            return True

        return a == b + 1 or a == b - 1

    @staticmethod
    def get_streaks(appearances: List[int]) -> List[int]:
        streaks = []
        current_streak = 0

        for i, appearance in enumerate(appearances):
            if current_streak == 0:
                current_streak += 1
            else:
                if LongestEinsteinStreakCalculator.are_years_consecutive(
                    appearance, appearances[i - 1]
                ):
                    current_streak += 1
                else:
                    streaks.append(current_streak)
                    current_streak = 1

        streaks.append(current_streak)
        return streaks

    def make_insight(self, year: Year) -> Optional[Insight]:
        if year != 0:
            return None

        streaks = {
            tk: LongestEinsteinStreakCalculator.get_streaks(appearances)
            for tk, appearances in self.einstein_appearances.items()
        }

        longest_streaks = {tk: max(streaks) for tk, streaks in streaks.items()}

        return make_leaderboard_from_dict_counts(
            longest_streaks,
            Insight.TYPED_LEADERBOARD_LONGEST_EINSTEIN_STREAK,
            year,
        )


class LongestQualifyingEventStreakCalculator(AbstractLeaderboardCalculator):
    def __init__(self):
        self.active_streaks = defaultdict(int)
        self.longest_streaks = defaultdict(int)

    def on_event(self, event: Event) -> None:
        if event.event_type_enum not in [EventType.DISTRICT, EventType.REGIONAL]:
            return

        winners = set()
        for award in event.awards:
            if award.award_type_enum == AwardType.WINNER:
                for team_key in award.team_list:
                    self.active_streaks[team_key.string_id()] += 1
                    self.longest_streaks[team_key.string_id()] = max(
                        self.longest_streaks[team_key.string_id()],
                        self.active_streaks[team_key.string_id()],
                    )
                    winners.add(team_key.string_id())

        for team in event.teams:
            if team.key_name not in winners and self.active_streaks[team.key_name] > 0:
                self.active_streaks[team.key_name] = 0

    def make_insight(self, year: Year) -> Optional[Insight]:
        if year != 0:
            return None

        for team_key, active_streak in self.active_streaks.items():
            if active_streak > 0:
                self.longest_streaks[team_key] = max(
                    self.longest_streaks[team_key], active_streak
                )

        return make_leaderboard_from_dict_counts(
            {k: v for k, v in self.longest_streaks.items() if v > 1},
            Insight.TYPED_LEADERBOARD_LONGEST_QUALIFYING_EVENT_STREAK,
            year,
        )


class InsightsLeaderboardTeamCalculator:
    @staticmethod
    def make_insights(
        year: Year, calculators: Optional[List[AbstractLeaderboardCalculator]] = None
    ) -> List[Insight]:
        if calculators is None:
            calculators = [
                MostBlueBannersCalculator(),
                MostAwardsCalculator(),
                MostNonChampsEventWinsCalculator(),
                MostMatchesPlayedCalculator(),
                MostEventsPlayedAtCalculator(),
                MostUniqueTeamsPlayedWithOrAgainstCalculator(),
                MostNonChampsImpactWinsCalculator(),
                MostWffasCalculator(),
                LongestEinsteinStreakCalculator(),
                LongestQualifyingEventStreakCalculator(),
            ]

        event_years = [year] if year != 0 else SeasonHelper.get_valid_years()
        for event_year in event_years:
            for event in EventListQuery(year=event_year).fetch():
                if event.event_type_enum not in SEASON_EVENT_TYPES:
                    continue

                event.prep_awards()
                event.prep_matches()
                event.prep_teams()

                for calculator in calculators:
                    calculator.on_event(event)

                event.clear_awards()
                event.clear_matches()
                event.clear_teams()

        insights = []
        for calculator in calculators:
            if insight := calculator.make_insight(year):
                insights.append(insight)

        return insights
