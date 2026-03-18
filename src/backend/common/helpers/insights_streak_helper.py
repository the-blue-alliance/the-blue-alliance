from collections import defaultdict
from typing import Dict, List, Optional, Set

from google.appengine.ext import ndb

from backend.common.consts.alliance_color import ALLIANCE_COLORS
from backend.common.consts.award_type import AwardType
from backend.common.consts.event_type import (
    EventType,
    NON_CMP_EVENT_TYPES,
    SEASON_EVENT_TYPES,
)
from backend.common.helpers.insights_helper_utils import (
    make_streak_insight,
    StreakState,
)
from backend.common.helpers.insights_leaderboard_team_helper import (
    AbstractLeaderboardCalculator,
)
from backend.common.helpers.season_helper import SeasonHelper
from backend.common.models.event import Event
from backend.common.models.insight import Insight
from backend.common.models.keys import TeamKey, Year
from backend.common.queries.event_query import EventListQuery


class ConsecutiveEventWinsCalculator(AbstractLeaderboardCalculator):
    def __init__(self) -> None:
        self.streak_states: Dict[TeamKey, StreakState] = defaultdict(StreakState)

    def on_event(self, event: Event) -> None:
        if event.event_type_enum not in [EventType.DISTRICT, EventType.REGIONAL]:
            return

        # Skip cancelled events with no matches (e.g. 2020)
        if len(event.matches) == 0:
            return

        winners: Set[TeamKey] = set()
        for award in event.awards:
            if award.award_type_enum == AwardType.WINNER:
                for team_key in award.team_list:
                    tk = team_key.string_id()
                    if tk is None:
                        continue
                    winners.add(tk)
                    self.streak_states[tk].increment(event.key_name)

        # For teams that attended but didn't win, break their streak
        for team in event.teams:
            tk = team.key_name
            if tk not in winners and self.streak_states[tk].active_streak > 0:
                self.streak_states[tk].finalize()

    def make_insight(self, year: Year) -> Optional[Insight]:
        if year != 0:
            return None

        return make_streak_insight(
            self.streak_states,
            Insight.TYPED_STREAK_CONSECUTIVE_EVENT_WINS,
            year,
        )


class ConsecutiveMatchWinsCalculator(AbstractLeaderboardCalculator):
    def __init__(self) -> None:
        self.streak_states: Dict[TeamKey, StreakState] = defaultdict(StreakState)

    def on_event(self, event: Event) -> None:
        for match in event.matches:
            if not match.has_been_played:
                continue

            match_key = match.key_name
            winning_alliance = match.winning_alliance
            if winning_alliance == "":
                # Tie — break streak for all teams in the match
                for team_key_name in match.team_key_names:
                    self.streak_states[team_key_name].finalize()
                continue

            # Determine winning and losing teams
            for color in ALLIANCE_COLORS:
                teams = match.alliances[color]["teams"]
                if color == winning_alliance:
                    for tk in teams:
                        self.streak_states[tk].increment(match_key)
                else:
                    for tk in teams:
                        self.streak_states[tk].finalize()

    def make_insight(self, year: Year) -> Optional[Insight]:
        if year != 0:
            return None

        return make_streak_insight(
            self.streak_states,
            Insight.TYPED_STREAK_CONSECUTIVE_MATCH_WINS,
            year,
        )


class ConsecutiveImpactWinsCalculator(AbstractLeaderboardCalculator):
    """Tracks consecutive years a team wins at least one Impact Award (Chairman's)."""

    def __init__(self) -> None:
        self.streak_states: Dict[TeamKey, StreakState] = defaultdict(StreakState)
        self.last_year_won: Dict[TeamKey, int] = {}
        self.current_year_winners: Set[TeamKey] = set()
        self._current_year: Optional[int] = None

    @staticmethod
    def are_years_consecutive(a: int, b: int) -> bool:
        """Check if two years are consecutive, accounting for COVID gap."""
        # 2020, 2021 had no/limited events
        if a in [2019, 2022] and b in [2019, 2022] and a != b:
            return True
        return abs(a - b) == 1

    def _finalize_year(self) -> None:
        """Called when we move to a new year — check which teams did NOT win this year."""
        if self._current_year is None:
            return

        for tk, state in list(self.streak_states.items()):
            if state.active_streak > 0 and tk not in self.current_year_winners:
                state.finalize()

    def on_event(self, event: Event) -> None:
        if event.year != self._current_year:
            if self._current_year is not None:
                self._finalize_year()
            self._current_year = event.year
            self.current_year_winners = set()

        for award in event.awards:
            if (
                award.award_type_enum == AwardType.CHAIRMANS
                and award.event_type_enum in NON_CMP_EVENT_TYPES
            ):
                for team_key in award.team_list:
                    tk = team_key.string_id()
                    if tk is None:
                        continue
                    if tk in self.current_year_winners:
                        continue  # Already counted for this year

                    self.current_year_winners.add(tk)
                    context = str(event.year)

                    state = self.streak_states[tk]
                    if tk in self.last_year_won:
                        if self.are_years_consecutive(
                            event.year, self.last_year_won[tk]
                        ):
                            state.increment(context)
                        else:
                            # Gap year(s) — break the streak
                            state.finalize()
                            state.increment(context)
                    else:
                        state.increment(context)

                    self.last_year_won[tk] = event.year

    def make_insight(self, year: Year) -> Optional[Insight]:
        if year != 0:
            return None

        # Finalize the last year being processed
        self._finalize_year()

        return make_streak_insight(
            self.streak_states,
            Insight.TYPED_STREAK_CONSECUTIVE_IMPACT_WINS,
            year,
        )


class InsightsStreakCalculator:
    @staticmethod
    def make_insights(
        year: Year,
        calculators: Optional[List[AbstractLeaderboardCalculator]] = None,
    ) -> List[Insight]:
        if calculators is None:
            calculators = [
                ConsecutiveEventWinsCalculator(),
                ConsecutiveMatchWinsCalculator(),
                ConsecutiveImpactWinsCalculator(),
            ]

        event_years = [year] if year != 0 else SeasonHelper.get_valid_years()
        for event_year in event_years:
            for event in EventListQuery(year=event_year).fetch():
                if event.event_type_enum not in SEASON_EVENT_TYPES:
                    continue

                event.prep_awards()
                event.prep_matches()
                event.prep_teams()

                event.matches.sort(key=lambda m: m.play_order)

                for calculator in calculators:
                    calculator.on_event(event)

                event.clear_awards()
                event.clear_matches()
                event.clear_teams()

                ndb.get_context().clear_cache()

        insights = []
        for calculator in calculators:
            if insight := calculator.make_insight(year):
                insights.append(insight)

        return insights
