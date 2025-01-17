import itertools
import json
import math
import statistics
from collections import defaultdict
from typing import Any, DefaultDict, Dict, List, NamedTuple, Tuple, TypedDict

import numpy as np
from google.appengine.ext import ndb
from pyre_extensions import none_throws

from backend.common.consts.alliance_color import AllianceColor
from backend.common.consts.award_type import AwardType, BLUE_BANNER_AWARDS
from backend.common.consts.comp_level import CompLevel, ELIM_LEVELS
from backend.common.consts.event_type import (
    CMP_EVENT_TYPES,
    EventType,
    NON_CMP_EVENT_TYPES,
    SEASON_EVENT_TYPES,
)
from backend.common.consts.insight_type import InsightType
from backend.common.futures import TypedFuture
from backend.common.helpers.event_helper import (
    EventHelper,
    OFFSEASON_EVENTS_LABEL,
    PRESEASON_EVENTS_LABEL,
)
from backend.common.helpers.event_insights_helper import EventInsightsHelper
from backend.common.models.award import Award
from backend.common.models.event import Event
from backend.common.models.insight import Insight, LeaderboardKeyType
from backend.common.models.keys import EventKey, MatchKey, TeamKey, Year
from backend.common.models.match import Match
from backend.common.models.team import Team


CounterDictType = DefaultDict[Any, int] | DefaultDict[Any, float] | Dict[Any, int]


class EventMatches(NamedTuple):
    event: Event
    matches: List[Match]


class WeekEventMatches(NamedTuple):
    week: str
    event_matches: List[EventMatches]


class LeaderboardRanking(TypedDict):
    keys: List[TeamKey | EventKey | MatchKey]
    value: int | float


class LeaderboardData(TypedDict):
    rankings: List[LeaderboardRanking]
    key_type: LeaderboardKeyType


class LeaderboardInsight(TypedDict):
    """This is the type that should be returned over the API!"""

    data: LeaderboardData
    name: str
    year: int


class NotableEntry(TypedDict):
    team_key: TeamKey

    # this needs to be a list to support overall
    # in an individual year, this should probably always be len 1
    context: List[EventKey]


class NotablesData(TypedDict):
    """In case we need more data in the future, we can add it here."""

    entries: List[NotableEntry]


class NotablesInsight(TypedDict):
    """This is the type that should be returned over the API!"""

    data: NotablesData
    name: str
    year: int


class InsightsHelper(object):
    """
    Helper for calculating insights and generating Insight objects
    """

    @classmethod
    def doMatchInsights(self, year: Year) -> List[Insight]:
        """
        Calculate match insights for a given year. Returns a list of Insights.
        """
        # Only fetch from DB once
        official_events = (
            Event.query(Event.year == year).order(Event.start_date).fetch(1000)
        )
        events_by_week = EventHelper.group_by_week(official_events)
        week_event_matches = (
            []
        )  # Tuples of: (week, events) where events are tuples of (event, matches)
        for week, events in events_by_week.items():
            if week in {OFFSEASON_EVENTS_LABEL, PRESEASON_EVENTS_LABEL}:
                continue
            event_matches = []
            for event in events:
                if not event.official:
                    continue
                event_matches.append(EventMatches(event=event, matches=event.matches))
            week_event_matches.append(
                WeekEventMatches(week=week, event_matches=event_matches)
            )

        insights = []
        insights += self._calculateHighscoreMatchesByWeek(week_event_matches, year)
        insights += self._calculateHighscoreMatches(week_event_matches, year)
        insights += self._calculateMatchAveragesByWeek(week_event_matches, year)
        insights += self._calculateMatchWinningMarginByWeek(week_event_matches, year)
        insights += self._calculateScoreDistribution(week_event_matches, year)
        insights += self._calculateWinningMarginDistribution(week_event_matches, year)
        insights += self._calculateNumMatches(week_event_matches, year)
        insights += self._calculateYearSpecific(week_event_matches, year)
        insights += self._calculateMatchesByTeam(week_event_matches, year)

        # leaderboard (exposed in API)
        insights += self._calculate_leaderboard_most_matches_played_by_team(
            week_event_matches, year
        )
        insights += self._calculate_leaderboard_most_events_played_at(
            week_event_matches, year
        )
        insights += self._calculate_leaderboard_highest_median_score_by_event(
            week_event_matches, year
        )
        insights += self._calculate_highest_clean_and_combined_scores(
            week_event_matches, year
        )
        insights += (
            self._calculate_leaderboard_most_unique_teams_played_with_or_against(
                week_event_matches, year
            )
        )

        return insights

    @classmethod
    def doAwardInsights(self, year: Year) -> List[Insight]:
        """
        Calculate award insights for a given year. Returns a list of Insights.
        """
        award_futures = ndb.get_multi_async(
            Award.query(
                Award.year == year, Award.event_type_enum.IN(SEASON_EVENT_TYPES)
            )
            .fetch_async(10000, keys_only=True)
            .get_result()
        )

        insights = []
        insights += self._calculateBlueBanners(award_futures, year)
        insights += self._calculateChampionshipStats(award_futures, year)
        insights += self._calculateRegionalStats(award_futures, year)
        insights += self._calculateSuccessfulElimTeamups(award_futures, year)

        # leaderboards (exposed in API)
        insights += self._calculate_assorted_award_leaderboards(award_futures, year)

        insights += self._calculate_notables_hall_of_fame(award_futures, year)
        insights += self._calculate_notables_division_winners_and_finals_appearances(
            award_futures, year
        )
        insights += self._calculate_notables_world_champions(award_futures, year)

        return insights

    @classmethod
    def doPredictionInsights(self, year: Year) -> List[Insight]:
        """
        Calculate aggregate prediction stats for all season events for a year.
        """

        events = Event.query(
            Event.event_type_enum.IN(SEASON_EVENT_TYPES),
            Event.year == (int(year)),
        ).fetch()
        for event in events:
            event.prep_details()
            event.prep_matches()

        has_insights = False
        correct_matches_count = defaultdict(int)
        total_matches_count = defaultdict(int)
        brier_scores = defaultdict(list)
        correct_matches_count_cmp = defaultdict(int)
        total_matches_count_cmp = defaultdict(int)
        brier_scores_cmp = defaultdict(list)
        for event in events:
            predictions = event.details.predictions if event.details else None
            if predictions:
                has_insights = True
                is_cmp = event.event_type_enum in CMP_EVENT_TYPES
                if "match_predictions" in predictions:
                    for match in event.matches:
                        if match.has_been_played:
                            level = (
                                "qual"
                                if match.comp_level == CompLevel.QM
                                else "playoff"
                            )

                            total_matches_count[level] += 1
                            if is_cmp:
                                total_matches_count_cmp[level] += 1

                            predicted_match = predictions["match_predictions"][
                                level
                            ].get(match.key.id())
                            if (
                                predicted_match
                                and match.winning_alliance
                                == predicted_match["winning_alliance"]
                            ):
                                correct_matches_count[level] += 1
                                if is_cmp:
                                    correct_matches_count_cmp[level] += 1

                for level in ["qual", "playoff"]:
                    if predictions.get("match_prediction_stats"):
                        bs = (
                            predictions.get("match_prediction_stats", {})
                            .get(level, {})
                            .get("brier_scores", {})
                        )
                        if bs:
                            brier_scores[level].append(bs["win_loss"])
                            if is_cmp:
                                brier_scores_cmp[level].append(bs["win_loss"])

        if not has_insights:
            data = None

        data = defaultdict(dict)
        for level in ["qual", "playoff"]:
            data[level]["mean_brier_score"] = (
                np.mean(np.asarray(brier_scores[level]))
                if brier_scores[level]
                else None
            )
            data[level]["correct_matches_count"] = correct_matches_count[level]
            data[level]["total_matches_count"] = total_matches_count[level]
            data[level]["mean_brier_score_cmp"] = (
                np.mean(np.asarray(brier_scores_cmp[level]))
                if brier_scores_cmp[level]
                else None
            )
            data[level]["correct_matches_count_cmp"] = correct_matches_count_cmp[level]
            data[level]["total_matches_count_cmp"] = total_matches_count_cmp[level]

        return [
            self._createInsight(
                data, Insight.INSIGHT_NAMES[Insight.MATCH_PREDICTIONS], year
            )
        ]

    @classmethod
    def _createInsight(self, data: Any, name: str, year: Year) -> Insight:
        """
        Create Insight object given data, name, and year
        """
        return Insight(
            id=Insight.render_key_name(year, name),
            name=name,
            year=year,
            data_json=json.dumps(data),
        )

    @classmethod
    def _create_leaderboard_from_dict_counts(
        cls,
        counter: CounterDictType,
        insight_type: int,
        year: int,
    ) -> Insight:
        sorted_leaderboard_tuples = cls._sort_counter_dict(
            counter, key_type=Insight.TYPED_LEADERBOARD_KEY_TYPES[insight_type]
        )
        leaderboard_rankings: List[LeaderboardRanking] = [
            LeaderboardRanking(keys=keys, value=value)
            for (value, keys) in sorted_leaderboard_tuples[:25]
        ]
        leaderboard_data = LeaderboardData(
            rankings=leaderboard_rankings,
            key_type=Insight.TYPED_LEADERBOARD_KEY_TYPES[insight_type],
        )

        return cls._createInsight(
            data=leaderboard_data,
            name=Insight.INSIGHT_NAMES[insight_type],
            year=year,
        )

    @classmethod
    def _create_notable_insight(
        cls,
        teams: Dict[TeamKey, List[EventKey]] | DefaultDict[TeamKey, List[EventKey]],
        insight_type: int,
        year: int,
    ) -> Insight:
        return cls._createInsight(
            data=NotablesData(
                entries=[
                    NotableEntry(team_key=team_key, context=context)
                    for team_key, context in teams.items()
                ]
            ),
            name=Insight.INSIGHT_NAMES[insight_type],
            year=year,
        )

    @classmethod
    def _calculate_assorted_award_leaderboards(
        cls, award_futures: List[TypedFuture[Award]], year: Year
    ) -> List[Insight]:
        banner_count = defaultdict(int)
        award_count = defaultdict(int)
        non_cmp_event_win_count = defaultdict(int)

        for award_future in award_futures:
            award = award_future.get_result()
            if award.award_type_enum == AwardType.WILDCARD:
                continue

            for team_key in award.team_list:
                award_count[team_key.id()] += 1

                if award.award_type_enum in BLUE_BANNER_AWARDS and award.count_banner:
                    banner_count[team_key.id()] += 1

                if (
                    award.award_type_enum == AwardType.WINNER
                    and award.event_type_enum in NON_CMP_EVENT_TYPES
                ):
                    non_cmp_event_win_count[team_key.id()] += 1

        return [
            cls._create_leaderboard_from_dict_counts(
                banner_count, Insight.TYPED_LEADERBOARD_BLUE_BANNERS, year
            ),
            cls._create_leaderboard_from_dict_counts(
                award_count, Insight.TYPED_LEADERBOARD_MOST_AWARDS, year
            ),
            cls._create_leaderboard_from_dict_counts(
                non_cmp_event_win_count,
                Insight.TYPED_LEADERBOARD_MOST_NON_CHAMPS_EVENT_WINS,
                year,
            ),
        ]

    @classmethod
    def _calculate_leaderboard_most_matches_played_by_team(
        cls, week_event_matches: List[WeekEventMatches], year: Year
    ) -> List[Insight]:
        counter = defaultdict(lambda: 0)
        for _, week_events in week_event_matches:
            for _, matches in week_events:
                for match in matches:
                    if match.has_been_played:
                        for alliance in match.alliances.values():
                            for tk in alliance["teams"]:
                                counter[tk] += 1

        return [
            cls._create_leaderboard_from_dict_counts(
                counter,
                Insight.TYPED_LEADERBOARD_MOST_MATCHES_PLAYED,
                year,
            )
        ]

    @classmethod
    def _calculate_leaderboard_most_events_played_at(
        cls, week_event_matches: List[WeekEventMatches], year: Year
    ) -> List[Insight]:
        events_played_at = defaultdict(set)
        for _, week_events in week_event_matches:
            for event, matches in week_events:
                for match in matches:
                    if match.has_been_played:
                        for alliance in match.alliances.values():
                            for tk in alliance["teams"]:
                                events_played_at[tk].add(event.key.id())

        counts = {tk: len(events) for tk, events in events_played_at.items()}
        return [
            cls._create_leaderboard_from_dict_counts(
                counts,
                Insight.TYPED_LEADERBOARD_MOST_EVENTS_PLAYED_AT,
                year,
            )
        ]

    @classmethod
    def _calculate_highest_clean_and_combined_scores(
        cls, week_event_matches: List[WeekEventMatches], year: Year
    ) -> List[Insight]:
        """Core logic is pretty much the same for both insights, so do both in 1 method."""
        match_winning_scores = defaultdict(int)
        match_combined_scores = defaultdict(int)

        for _, week_events in week_event_matches:
            for _, matches in week_events:
                for match in matches:
                    if match.has_been_played:
                        redScore = int(match.alliances[AllianceColor.RED]["score"])
                        blueScore = int(match.alliances[AllianceColor.BLUE]["score"])

                        if year >= 2016:
                            if match.score_breakdown:
                                redScore -= none_throws(match.score_breakdown)[
                                    AllianceColor.RED
                                ].get("foulPoints", 0)
                                blueScore -= none_throws(match.score_breakdown)[
                                    AllianceColor.BLUE
                                ].get("foulPoints", 0)

                        match_winning_scores[match.key.id()] = max(redScore, blueScore)
                        match_combined_scores[match.key.id()] = redScore + blueScore

        return [
            cls._create_leaderboard_from_dict_counts(
                match_winning_scores,
                Insight.TYPED_LEADERBOARD_HIGHEST_MATCH_CLEAN_SCORE,
                year,
            ),
            cls._create_leaderboard_from_dict_counts(
                match_combined_scores,
                Insight.TYPED_LEADERBOARD_HIGHEST_MATCH_CLEAN_COMBINED_SCORE,
                year,
            ),
        ]

    @classmethod
    def _calculate_leaderboard_highest_median_score_by_event(
        cls, week_event_matches: List[WeekEventMatches], year: Year
    ) -> List[Insight]:
        scores = defaultdict(list)
        for _, week_events in week_event_matches:
            for event, matches in week_events:
                for match in matches:
                    if match.has_been_played:
                        scores[event.key.id()].append(
                            match.alliances[AllianceColor.RED]["score"]
                        )
                        scores[event.key.id()].append(
                            match.alliances[AllianceColor.BLUE]["score"]
                        )

        medians = defaultdict(int)
        for event_key, scores_list in scores.items():
            if len(scores_list) < 10:
                continue

            medians[event_key] = statistics.median(sorted(scores_list))

        return [
            cls._create_leaderboard_from_dict_counts(
                medians,
                Insight.TYPED_LEADERBOARD_HIGHEST_MEDIAN_SCORE_BY_EVENT,
                year,
            )
        ]

    @classmethod
    def _calculate_leaderboard_most_unique_teams_played_with_or_against(
        cls, week_event_matches: List[WeekEventMatches], year: Year
    ) -> List[Insight]:
        met_teams_set = defaultdict(set)
        for _, week_events in week_event_matches:
            for _, matches in week_events:
                for match in matches:
                    if match.has_been_played:
                        all_teams = (
                            match.alliances[AllianceColor.RED]["teams"]
                            + match.alliances[AllianceColor.BLUE]["teams"]
                        )

                        for team in all_teams:
                            for other_team in all_teams:
                                if team != other_team:
                                    met_teams_set[team].add(other_team)

        counter = {tk: len(met_teams) for tk, met_teams in met_teams_set.items()}
        return [
            cls._create_leaderboard_from_dict_counts(
                counter,
                Insight.TYPED_LEADERBOARD_MOST_UNIQUE_TEAMS_PLAYED_WITH_AGAINST,
                year,
            )
        ]

    @classmethod
    def _calculate_notables_from_einstein_award(
        cls,
        award_futures: List[TypedFuture[Award]],
        year: Year,
        award_type: AwardType,
        insight_type: int,
    ) -> List[Insight]:
        team_context_map: Dict[TeamKey, List[EventKey]] = {}
        for award_future in award_futures:
            award = award_future.get_result()
            if (
                award.event_type_enum == EventType.CMP_FINALS
                and award.award_type_enum == award_type
            ):
                for tk in award.team_list:
                    team_context_map[str(tk.id())] = [str(award.event.id())]

        return [
            cls._create_notable_insight(
                team_context_map,
                insight_type,
                year,
            )
        ]

    @classmethod
    def _calculate_notables_hall_of_fame(
        cls, award_futures: List[TypedFuture[Award]], year: Year
    ):
        return cls._calculate_notables_from_einstein_award(
            award_futures,
            year,
            AwardType.CHAIRMANS,
            Insight.TYPED_NOTABLES_HALL_OF_FAME,
        )

    @classmethod
    def _calculate_notables_world_champions(
        cls, award_futures: List[TypedFuture[Award]], year: Year
    ) -> List[Insight]:
        return cls._calculate_notables_from_einstein_award(
            award_futures,
            year,
            AwardType.WINNER,
            Insight.TYPED_NOTABLES_WORLD_CHAMPIONS,
        )

    @classmethod
    def _calculate_notables_division_winners_and_finals_appearances(
        cls, award_futures: List[TypedFuture[Award]], year: Year
    ):
        winner_context_map: Dict[TeamKey, List[EventKey]] = {}
        finals_appearance_map: Dict[TeamKey, List[EventKey]] = {}

        for award_future in award_futures:
            award = award_future.get_result()
            if (
                award.event_type_enum == EventType.CMP_DIVISION
                and award.award_type_enum == AwardType.WINNER
            ):
                for tk in award.team_list:
                    winner_context_map[str(tk.id())] = [str(award.event.id())]
                    finals_appearance_map[str(tk.id())] = [str(award.event.id())]

            if (
                award.event_type_enum == EventType.CMP_DIVISION
                and award.award_type_enum == AwardType.FINALIST
            ):
                for tk in award.team_list:
                    finals_appearance_map[str(tk.id())] = [str(award.event.id())]

        return [
            cls._create_notable_insight(
                winner_context_map,
                Insight.TYPED_NOTABLES_DIVISION_WINNERS,
                year,
            ),
            cls._create_notable_insight(
                finals_appearance_map,
                Insight.TYPED_NOTABLES_DIVISION_FINALS_APPEARANCES,
                year,
            ),
        ]

    @classmethod
    def _generateMatchData(self, match: Match, event: Event) -> Dict:
        """
        A dict of any data needed for front-end rendering
        """
        return {
            "key_name": match.key_name,
            "verbose_name": match.verbose_name,
            "event_name": event.name,
            "alliances": match.alliances,
            "score_breakdown": match.score_breakdown,
            "winning_alliance": match.winning_alliance,
            "tba_video": None,
            "youtube_videos_formatted": match.youtube_videos_formatted,
        }

    @classmethod
    def _sort_counter_dict(
        cls, count: CounterDictType, key_type: LeaderboardKeyType = "team"
    ) -> List[Tuple[int | float, List[str]]]:
        """
        Takes an object that looks like: {"frc1": 5, "frc2": 5, "frc3": 3}
        (may be match, event, or team keys) and returns a list of tuples that
        are (magnitude, list of keys) grouped by magnitude, and then sorted by
        magnitude, e.g. [(5, ["frc1", "frc2"]), (2, ["frc3"])].
        """

        # sort by:
        #   team: team number
        #   event & match: alphabetically by key
        tuples = []
        if key_type == "team":
            tuples = sorted(count.items(), key=lambda pair: int(pair[0][3:]))
        else:
            tuples = sorted(count.items(), key=lambda pair: pair[4:])

        # group by magnitude
        temp = defaultdict(list)
        for team, num in tuples:
            temp[num].append(team)

        # sort by magnitude
        return sorted(temp.items(), key=lambda pair: float(pair[0]), reverse=True)

    @classmethod
    def _sortTeamYearWinsDict(self, wins_dict):
        """
        Sorts dicts with key: number of wins, value: list of (team, years)
        by number of wins and by team number
        """
        wins_dict = sorted(
            wins_dict.items(), key=lambda pair: int(pair[0][3:])
        )  # Sort by team number
        temp = defaultdict(list)
        for team, year_wins in wins_dict:
            temp[len(year_wins)].append((team, sorted(year_wins)))
        return sorted(
            temp.items(), key=lambda pair: int(pair[0]), reverse=True
        )  # Sort by win number

    @classmethod
    def _sortTeamList(self, team_list: List[Team]) -> List[Team]:
        """
        Sorts list of teams
        """
        return sorted(team_list, key=lambda team: int(team[3:]))  # Sort by team number

    @classmethod
    def _calculateHighscoreMatchesByWeek(
        self, week_event_matches: List[WeekEventMatches], year: Year
    ) -> List[Insight]:
        """
        Returns an Insight where the data is a list of tuples:
        (week string, list of highest scoring matches)
        """
        highscore_matches_by_week = (
            []
        )  # tuples: week, list of matches (if there are ties)
        for week, week_events in week_event_matches:
            week_highscore_matches = []
            highscore = 0
            for event, matches in week_events:
                for match in matches:
                    redScore = int(match.alliances[AllianceColor.RED]["score"])
                    blueScore = int(match.alliances[AllianceColor.BLUE]["score"])
                    maxScore = max(redScore, blueScore)
                    if maxScore >= highscore:
                        if maxScore > highscore:
                            week_highscore_matches = []
                        week_highscore_matches.append(
                            self._generateMatchData(match, event)
                        )
                        highscore = maxScore
            highscore_matches_by_week.append((week, week_highscore_matches))

        insight = None
        if highscore_matches_by_week != []:
            insight = self._createInsight(
                highscore_matches_by_week,
                Insight.INSIGHT_NAMES[Insight.MATCH_HIGHSCORE_BY_WEEK],
                year,
            )
        if insight is not None:
            return [insight]
        else:
            return []

    @classmethod
    def _calculateHighscoreMatches(
        self, week_event_matches: List[WeekEventMatches], year: Year
    ) -> List[Insight]:
        """
        Returns an Insight where the data is list of highest scoring matches
        """
        highscore_matches = {
            "qual": [],
            "playoff": [],
            "overall": [],
        }  # dict of list of matches (if there are ties)
        highscore = {
            "qual": 0,
            "playoff": 0,
            "overall": 0,
        }
        for _, week_events in week_event_matches:
            for event, matches in week_events:
                for match in matches:
                    comp_level = (
                        "qual" if match.comp_level == CompLevel.QM else "playoff"
                    )
                    match_data = self._generateMatchData(match, event)

                    redScore = int(match.alliances[AllianceColor.RED]["score"])
                    blueScore = int(match.alliances[AllianceColor.BLUE]["score"])

                    # Overall, including penalties
                    maxScore = max(redScore, blueScore)
                    if maxScore >= highscore["overall"]:
                        if maxScore > highscore["overall"]:
                            highscore_matches["overall"] = []
                        highscore_matches["overall"].append(match_data)
                        highscore["overall"] = maxScore

                    # Penalty free, if possible
                    if year >= 2017:
                        if match.score_breakdown:
                            redScore -= none_throws(match.score_breakdown)[
                                AllianceColor.RED
                            ].get("foulPoints", 0)
                            blueScore -= none_throws(match.score_breakdown)[
                                AllianceColor.BLUE
                            ].get("foulPoints", 0)

                    maxScore = max(redScore, blueScore)
                    if maxScore >= highscore[comp_level]:
                        if maxScore > highscore[comp_level]:
                            highscore_matches[comp_level] = []
                        highscore_matches[comp_level].append(match_data)
                        highscore[comp_level] = maxScore

        insight = None
        if highscore_matches != []:
            insight = self._createInsight(
                highscore_matches, Insight.INSIGHT_NAMES[Insight.MATCH_HIGHSCORE], year
            )
        if insight is not None:
            return [insight]
        else:
            return []

    @classmethod
    def _calculateMatchesByTeam(
        self, week_event_matches: List[WeekEventMatches], year: Year
    ) -> List[Insight]:
        counter = defaultdict(lambda: 0)
        for _, week_events in week_event_matches:
            for _, matches in week_events:
                for match in matches:
                    if match.has_been_played:
                        for alliance in match.alliances.values():
                            for tk in alliance["teams"]:
                                counter[tk] += 1

        grouped_by_win_count = self._sort_counter_dict(counter)

        return [
            self._createInsight(
                data=grouped_by_win_count,
                name=Insight.INSIGHT_NAMES[Insight.MATCHES_PLAYED],
                year=year,
            )
        ]

    @classmethod
    def _calculateMatchAveragesByWeek(
        self, week_event_matches: List[WeekEventMatches], year: Year
    ) -> List[Insight]:
        """
        Returns a list of Insights, one for all data and one for elim data
        The data for each Insight is a list of tuples:
        (week string, match averages)
        """
        match_averages_by_week = []  # tuples: week, average score
        elim_match_averages_by_week = []  # tuples: week, average score
        for week, week_events in week_event_matches:
            week_match_sum = 0
            num_matches_by_week = 0
            elim_week_match_sum = 0
            elim_num_matches_by_week = 0
            for _, matches in week_events:
                for match in matches:
                    if not match.has_been_played:
                        continue
                    redScore = int(match.alliances[AllianceColor.RED]["score"])
                    blueScore = int(match.alliances[AllianceColor.BLUE]["score"])
                    week_match_sum += redScore + blueScore
                    num_matches_by_week += 1
                    if match.comp_level in ELIM_LEVELS:
                        elim_week_match_sum += redScore + blueScore
                        elim_num_matches_by_week += 1

            if num_matches_by_week != 0:
                week_average = float(week_match_sum) / num_matches_by_week / 2
                match_averages_by_week.append((week, week_average))

            if elim_num_matches_by_week != 0:
                elim_week_average = (
                    float(elim_week_match_sum) / elim_num_matches_by_week / 2
                )
                elim_match_averages_by_week.append((week, elim_week_average))

        insights = []
        if match_averages_by_week != []:
            insights.append(
                self._createInsight(
                    match_averages_by_week,
                    Insight.INSIGHT_NAMES[Insight.MATCH_AVERAGES_BY_WEEK],
                    year,
                )
            )
        if elim_match_averages_by_week != []:
            insights.append(
                self._createInsight(
                    elim_match_averages_by_week,
                    Insight.INSIGHT_NAMES[Insight.ELIM_MATCH_AVERAGES_BY_WEEK],
                    year,
                )
            )
        return insights

    @classmethod
    def _calculateMatchWinningMarginByWeek(
        self, week_event_matches: List[WeekEventMatches], year: Year
    ) -> List[Insight]:
        """
        Returns a list of Insights, one for all data and one for elim data
        The data for each Insight is a list of tuples:
        (week string, match average margins)
        """
        match_average_margins_by_week = []  # tuples: week, average margin
        elim_match_average_margins_by_week = []  # tuples: week, average margin
        for week, week_events in week_event_matches:
            week_match_margin_sum = 0
            num_matches_by_week = 0
            elim_week_match_margin_sum = 0
            elim_num_matches_by_week = 0
            for _, matches in week_events:
                for match in matches:
                    if not match.has_been_played:
                        continue
                    redScore = int(match.alliances[AllianceColor.RED]["score"])
                    blueScore = int(match.alliances[AllianceColor.BLUE]["score"])
                    week_match_margin_sum += abs(redScore - blueScore)
                    num_matches_by_week += 1
                    if match.comp_level in ELIM_LEVELS:
                        elim_week_match_margin_sum += abs(redScore - blueScore)
                        elim_num_matches_by_week += 1

            if num_matches_by_week != 0:
                week_average = float(week_match_margin_sum) / num_matches_by_week
                match_average_margins_by_week.append((week, week_average))

            if elim_num_matches_by_week != 0:
                elim_week_average = (
                    float(elim_week_match_margin_sum) / elim_num_matches_by_week
                )
                elim_match_average_margins_by_week.append((week, elim_week_average))

        insights = []
        if match_average_margins_by_week != []:
            insights.append(
                self._createInsight(
                    match_average_margins_by_week,
                    Insight.INSIGHT_NAMES[Insight.MATCH_AVERAGE_MARGINS_BY_WEEK],
                    year,
                )
            )
        if elim_match_average_margins_by_week != []:
            insights.append(
                self._createInsight(
                    elim_match_average_margins_by_week,
                    Insight.INSIGHT_NAMES[Insight.ELIM_MATCH_AVERAGE_MARGINS_BY_WEEK],
                    year,
                )
            )
        return insights

    @classmethod
    def _calculateScoreDistribution(
        self, week_event_matches: List[WeekEventMatches], year: Year
    ) -> List[Insight]:
        """
        Returns a list of Insights, one for all data and one for elim data
        The data for each Insight is a dict:
        Key: Middle score of a bucketed range of scores, Value: % occurrence
        """
        score_distribution = defaultdict(int)
        elim_score_distribution = defaultdict(int)
        overall_highscore = 0
        for _, week_events in week_event_matches:
            for _, matches in week_events:
                for match in matches:
                    if not match.has_been_played:
                        continue
                    redScore = int(match.alliances[AllianceColor.RED]["score"])
                    blueScore = int(match.alliances[AllianceColor.BLUE]["score"])

                    overall_highscore = max(overall_highscore, redScore, blueScore)

                    score_distribution[redScore] += 1
                    score_distribution[blueScore] += 1

                    if match.comp_level in ELIM_LEVELS:
                        elim_score_distribution[redScore] += 1
                        elim_score_distribution[blueScore] += 1

        insights = []
        binAmount = None
        if score_distribution != {}:
            binAmount = math.ceil(float(overall_highscore) / 20)
            totalCount = float(sum(score_distribution.values()))
            score_distribution_normalized = {}
            for score, amount in score_distribution.items():
                roundedScore = (
                    score - int(score % binAmount) + binAmount / 2
                )  # Round off and then center in the bin
                contribution = float(amount) * 100 / totalCount
                if roundedScore in score_distribution_normalized:
                    score_distribution_normalized[roundedScore] += contribution
                else:
                    score_distribution_normalized[roundedScore] = contribution
            insights.append(
                self._createInsight(
                    score_distribution_normalized,
                    Insight.INSIGHT_NAMES[Insight.SCORE_DISTRIBUTION],
                    year,
                )
            )
        if elim_score_distribution != {}:
            if binAmount is None:  # Use same binAmount from above if possible
                binAmount = math.ceil(float(overall_highscore) / 20)
            totalCount = float(sum(elim_score_distribution.values()))
            elim_score_distribution_normalized = {}
            for score, amount in elim_score_distribution.items():
                roundedScore = score - int(score % binAmount) + binAmount / 2
                contribution = float(amount) * 100 / totalCount
                if roundedScore in elim_score_distribution_normalized:
                    elim_score_distribution_normalized[roundedScore] += contribution
                else:
                    elim_score_distribution_normalized[roundedScore] = contribution
            insights.append(
                self._createInsight(
                    elim_score_distribution_normalized,
                    Insight.INSIGHT_NAMES[Insight.ELIM_SCORE_DISTRIBUTION],
                    year,
                )
            )

        return insights

    @classmethod
    def _calculateWinningMarginDistribution(
        self, week_event_matches: List[WeekEventMatches], year: Year
    ) -> List[Insight]:
        """
        Returns a list of Insights, one for all data and one for elim data
        The data for each Insight is a dict:
        Key: Middle score of a bucketed range of scores, Value: % occurrence
        """
        winning_margin_distribution = defaultdict(int)
        elim_winning_margin_distribution = defaultdict(int)
        overall_high_margin = 0
        for _, week_events in week_event_matches:
            for _, matches in week_events:
                for match in matches:
                    if not match.has_been_played:
                        continue
                    redScore = int(match.alliances[AllianceColor.RED]["score"])
                    blueScore = int(match.alliances[AllianceColor.BLUE]["score"])

                    winning_margin = abs(redScore - blueScore)

                    overall_high_margin = max(overall_high_margin, winning_margin)

                    winning_margin_distribution[winning_margin] += 1

                    if match.comp_level in ELIM_LEVELS:
                        elim_winning_margin_distribution[winning_margin] += 1

        insights = []
        binAmount = None
        if winning_margin_distribution != {}:
            binAmount = math.ceil(float(overall_high_margin) / 20)
            totalCount = float(sum(winning_margin_distribution.values()))
            winning_margin_distribution_normalized = {}
            for margin, amount in winning_margin_distribution.items():
                roundedScore = (
                    margin - int(margin % binAmount) + binAmount / 2
                )  # Round off and then center in the bin
                contribution = float(amount) * 100 / totalCount
                if roundedScore in winning_margin_distribution_normalized:
                    winning_margin_distribution_normalized[roundedScore] += contribution
                else:
                    winning_margin_distribution_normalized[roundedScore] = contribution

            insights.append(
                self._createInsight(
                    winning_margin_distribution_normalized,
                    Insight.INSIGHT_NAMES[Insight.WINNING_MARGIN_DISTRIBUTION],
                    year,
                )
            )

        if elim_winning_margin_distribution != {}:
            if binAmount is None:  # Use same binAmount from above if possible
                binAmount = math.ceil(float(overall_high_margin) / 20)
            totalCount = float(sum(elim_winning_margin_distribution.values()))
            elim_winning_margin_distribution_normalized = {}
            for margin, amount in elim_winning_margin_distribution.items():
                roundedScore = margin - int(margin % binAmount) + binAmount / 2
                contribution = float(amount) * 100 / totalCount
                if roundedScore in elim_winning_margin_distribution_normalized:
                    elim_winning_margin_distribution_normalized[
                        roundedScore
                    ] += contribution
                else:
                    elim_winning_margin_distribution_normalized[roundedScore] = (
                        contribution
                    )

            insights.append(
                self._createInsight(
                    elim_winning_margin_distribution_normalized,
                    Insight.INSIGHT_NAMES[Insight.ELIM_WINNING_MARGIN_DISTRIBUTION],
                    year,
                )
            )

        return insights

    @classmethod
    def _calculateNumMatches(
        self, week_event_matches: List[WeekEventMatches], year: Year
    ) -> List[Insight]:
        """
        Returns an Insight where the data is the number of matches
        """
        numMatches = 0
        for _, week_events in week_event_matches:
            for _, matches in week_events:
                numMatches += len(matches)

        return [
            self._createInsight(
                numMatches, Insight.INSIGHT_NAMES[Insight.NUM_MATCHES], year
            )
        ]

    @classmethod
    def _calculateYearSpecific(
        self, week_event_matches: List[WeekEventMatches], year: Year
    ) -> List[Insight]:
        """
        Returns an Insight where the data contains year specific insights
        """
        all_matches = []
        event_insights_by_week = []  # tuples: week, week_insights
        for week, week_events in week_event_matches:
            week_matches = []
            for _, matches in week_events:
                week_matches += matches
                all_matches += matches
            week_insights = EventInsightsHelper.calculate_event_insights(
                week_matches, year
            )
            if week_insights:
                event_insights_by_week.append((week, week_insights))

        total_insights = EventInsightsHelper.calculate_event_insights(all_matches, year)

        insights = []
        if event_insights_by_week != []:
            insights.append(
                self._createInsight(
                    event_insights_by_week,
                    Insight.INSIGHT_NAMES[Insight.YEAR_SPECIFIC_BY_WEEK],
                    year,
                )
            )
        if total_insights:
            insights.append(
                self._createInsight(
                    total_insights, Insight.INSIGHT_NAMES[Insight.YEAR_SPECIFIC], year
                )
            )

        return insights

    @classmethod
    def _calculateBlueBanners(
        self, award_futures: List[TypedFuture[Award]], year: Year
    ) -> List[Insight]:
        """
        Returns an Insight where the data is a dict:
        Key: number of blue banners, Value: list of teams with that number of blue banners
        """
        blue_banner_winners = defaultdict(int)
        for award_future in award_futures:
            award = award_future.get_result()
            if award.award_type_enum in BLUE_BANNER_AWARDS and award.count_banner:
                for team_key in award.team_list:
                    team_key_name = team_key.id()
                    blue_banner_winners[team_key_name] += 1
        blue_banner_winners = self._sort_counter_dict(blue_banner_winners)

        insight = None
        if blue_banner_winners != []:
            insight = self._createInsight(
                blue_banner_winners, Insight.INSIGHT_NAMES[Insight.BLUE_BANNERS], year
            )
        if insight is not None:
            return [insight]
        else:
            return []

    @classmethod
    def _calculateChampionshipStats(
        self, award_futures: List[TypedFuture[Award]], year: Year
    ) -> List[Insight]:
        """
        Returns a list of Insights where, depending on the Insight, the data
        is either a team or a list of teams
        """
        ca_winner = None
        world_champions = []
        world_finalists = []
        division_winners = []
        division_finalists = []
        for award_future in award_futures:
            award = award_future.get_result()
            for team_key in award.team_list:
                team_key_name = team_key.id()
                if award.event_type_enum == EventType.CMP_FINALS:
                    if award.award_type_enum == AwardType.CHAIRMANS:
                        ca_winner = team_key_name
                    elif award.award_type_enum == AwardType.WINNER:
                        world_champions.append(team_key_name)
                    elif award.award_type_enum == AwardType.FINALIST:
                        world_finalists.append(team_key_name)
                elif award.event_type_enum == EventType.CMP_DIVISION:
                    if award.award_type_enum == AwardType.WINNER:
                        division_winners.append(team_key_name)
                    elif award.award_type_enum == AwardType.FINALIST:
                        division_finalists.append(team_key_name)

        world_champions = self._sortTeamList(world_champions)
        world_finalists = self._sortTeamList(world_finalists)
        division_winners = self._sortTeamList(division_winners)
        division_finalists = self._sortTeamList(division_finalists)

        insights = []
        if ca_winner is not None:
            insights += [
                self._createInsight(
                    ca_winner, Insight.INSIGHT_NAMES[Insight.CA_WINNER], year
                )
            ]
        if world_champions != []:
            insights += [
                self._createInsight(
                    world_champions,
                    Insight.INSIGHT_NAMES[Insight.WORLD_CHAMPIONS],
                    year,
                )
            ]
        if world_finalists != []:
            insights += [
                self._createInsight(
                    world_finalists,
                    Insight.INSIGHT_NAMES[Insight.WORLD_FINALISTS],
                    year,
                )
            ]
        if division_winners != []:
            insights += [
                self._createInsight(
                    division_winners,
                    Insight.INSIGHT_NAMES[Insight.DIVISION_WINNERS],
                    year,
                )
            ]
        if division_finalists != []:
            insights += [
                self._createInsight(
                    division_finalists,
                    Insight.INSIGHT_NAMES[Insight.DIVISION_FINALISTS],
                    year,
                )
            ]
        return insights

    @classmethod
    def _calculateRegionalStats(
        self, award_futures: List[TypedFuture[Award]], year: Year
    ) -> List[Insight]:
        """
        Returns a list of Insights where, depending on the Insight, the data
        is either a list of teams or a dict:
        Key: number of wins, Value: list of teams with that number of wins
        """
        rca_winners = []
        regional_winners = defaultdict(int)
        for award_future in award_futures:
            award = award_future.get_result()
            if award.event_type_enum in CMP_EVENT_TYPES:
                continue
            for team_key in award.team_list:
                team_key_name = team_key.id()
                if (
                    award.award_type_enum == AwardType.CHAIRMANS
                    and award.event_type_enum
                    in {EventType.REGIONAL, EventType.DISTRICT_CMP}
                ):
                    # Only count Chairman's at regionals and district championships
                    rca_winners.append(team_key_name)
                elif award.award_type_enum == AwardType.WINNER:
                    regional_winners[team_key_name] += 1

        rca_winners = self._sortTeamList(rca_winners)
        regional_winners = self._sort_counter_dict(regional_winners)

        insights = []
        if rca_winners != []:
            insights += [
                self._createInsight(
                    rca_winners, Insight.INSIGHT_NAMES[Insight.RCA_WINNERS], year
                )
            ]
        if regional_winners != []:
            insights += [
                self._createInsight(
                    regional_winners,
                    Insight.INSIGHT_NAMES[Insight.REGIONAL_DISTRICT_WINNERS],
                    year,
                )
            ]
        return insights

    @classmethod
    def _calculateSuccessfulElimTeamups(
        self, award_futures: List[TypedFuture[Award]], year: Year
    ) -> List[Insight]:
        """
        Returns an Insight where the data is a list of list of teams that won an event together
        """
        successful_elim_teamups = []
        for award_future in award_futures:
            award = award_future.get_result()
            if award.award_type_enum == AwardType.WINNER:
                successful_elim_teamups.append(
                    [team_key.id() for team_key in award.team_list]
                )

        if successful_elim_teamups != []:
            return [
                self._createInsight(
                    successful_elim_teamups,
                    Insight.INSIGHT_NAMES[Insight.SUCCESSFUL_ELIM_TEAMUPS],
                    year,
                )
            ]
        else:
            return []

    @classmethod
    def doOverallMatchInsights(self) -> List[Insight]:
        """
        Calculate match insights across all years. Returns a list of Insights.
        """
        insights = []

        year_num_matches = Insight.query(
            Insight.name == Insight.INSIGHT_NAMES[Insight.NUM_MATCHES],
            Insight.year != 0,
        ).fetch(1000)
        num_matches = []
        for insight in year_num_matches:
            num_matches.append((insight.year, insight.data))

        # Creating Insights
        if num_matches:
            insights.append(
                self._createInsight(
                    num_matches, Insight.INSIGHT_NAMES[Insight.NUM_MATCHES], 0
                )
            )

        insights.extend(
            self.do_overall_leaderboard_insights(insight_type=InsightType.MATCHES)
        )

        return insights

    @classmethod
    def doOverallAwardInsights(self) -> List[Insight]:
        """
        Calculate award insights across all years. Returns a list of Insights.
        """
        insights = []

        year_regional_winners = Insight.query(
            Insight.name == Insight.INSIGHT_NAMES[Insight.REGIONAL_DISTRICT_WINNERS],
            Insight.year != 0,
        ).fetch(1000)
        regional_winners = defaultdict(int)
        for insight in year_regional_winners:
            for number, team_list in insight.data:
                for team in team_list:
                    regional_winners[team] += number

        year_blue_banners = Insight.query(
            Insight.name == Insight.INSIGHT_NAMES[Insight.BLUE_BANNERS],
            Insight.year != 0,
        ).fetch(1000)
        blue_banners = defaultdict(int)
        for insight in year_blue_banners:
            for number, team_list in insight.data:
                for team in team_list:
                    blue_banners[team] += number

        year_rca_winners = Insight.query(
            Insight.name == Insight.INSIGHT_NAMES[Insight.RCA_WINNERS],
            Insight.year != 0,
        ).fetch(1000)
        rca_winners = defaultdict(int)
        for insight in year_rca_winners:
            for team in insight.data:
                rca_winners[team] += 1

        year_world_champions = Insight.query(
            Insight.name == Insight.INSIGHT_NAMES[Insight.WORLD_CHAMPIONS],
            Insight.year != 0,
        ).fetch(1000)
        world_champions = defaultdict(list)
        for insight in year_world_champions:
            for team in insight.data:
                world_champions[team].append(insight.year)

        year_division_winners = Insight.query(
            Insight.name == Insight.INSIGHT_NAMES[Insight.DIVISION_WINNERS],
            Insight.year != 0,
        ).fetch(1000)
        division_winners = defaultdict(list)
        for insight in year_division_winners:
            for team in insight.data:
                division_winners[team].append(insight.year)

        einstein_streak = defaultdict(int)
        for team, years in division_winners.items():
            streak = 1
            last_year = years[0]
            for year in years[1:]:
                if year == last_year + 1:
                    streak += 1
                else:
                    streak = 1
                # There was no championship in 2020 and 2021
                last_year = 2021 if year == 2019 else year
            einstein_streak[team] = streak

        year_successful_elim_teamups = Insight.query(
            Insight.name == Insight.INSIGHT_NAMES[Insight.SUCCESSFUL_ELIM_TEAMUPS],
            Insight.year != 0,
        ).fetch(1000)
        successful_elim_teamups = defaultdict(int)
        for insight in year_successful_elim_teamups:
            for teams in insight.data:
                for pairs in itertools.combinations(teams, 2):
                    successful_elim_teamups[tuple(sorted(pairs))] += 1
        successful_elim_teamups_sorted = defaultdict(list)
        for teams, num_wins in successful_elim_teamups.items():
            sorted_teams = sorted(teams, key=lambda team_key: int(team_key[3:]))
            successful_elim_teamups_sorted[num_wins].append(sorted_teams)
        successful_elim_teamups_sorted = sorted(
            successful_elim_teamups_sorted.items(), key=lambda x: -x[0]
        )

        # Sorting
        regional_winners = self._sort_counter_dict(regional_winners)
        blue_banners = self._sort_counter_dict(blue_banners)
        rca_winners = self._sort_counter_dict(rca_winners)
        world_champions = self._sortTeamYearWinsDict(world_champions)
        division_winners = self._sortTeamYearWinsDict(division_winners)
        einstein_streak = self._sort_counter_dict(einstein_streak)

        # Creating Insights
        if regional_winners:
            insights.append(
                self._createInsight(
                    regional_winners,
                    Insight.INSIGHT_NAMES[Insight.REGIONAL_DISTRICT_WINNERS],
                    0,
                )
            )

        if blue_banners:
            insights.append(
                self._createInsight(
                    blue_banners, Insight.INSIGHT_NAMES[Insight.BLUE_BANNERS], 0
                )
            )

        if rca_winners:
            insights.append(
                self._createInsight(
                    rca_winners, Insight.INSIGHT_NAMES[Insight.RCA_WINNERS], 0
                )
            )

        if world_champions:
            insights.append(
                self._createInsight(
                    world_champions, Insight.INSIGHT_NAMES[Insight.WORLD_CHAMPIONS], 0
                )
            )

        if division_winners:
            insights.append(
                self._createInsight(
                    division_winners, Insight.INSIGHT_NAMES[Insight.DIVISION_WINNERS], 0
                )
            )

        if einstein_streak:
            insights.append(
                self._createInsight(
                    einstein_streak, Insight.INSIGHT_NAMES[Insight.EINSTEIN_STREAK], 0
                )
            )

        if year_successful_elim_teamups:
            insights.append(
                self._createInsight(
                    successful_elim_teamups_sorted,
                    Insight.INSIGHT_NAMES[Insight.SUCCESSFUL_ELIM_TEAMUPS],
                    0,
                )
            )

        insights.extend(
            self.do_overall_leaderboard_insights(insight_type=InsightType.AWARDS)
        )
        insights.extend(self._do_overall_notable_insights())

        return insights

    @classmethod
    def do_overall_leaderboard_insights(
        cls, insight_type: InsightType
    ) -> List[Insight]:
        insight_types: set[int] = set()
        if insight_type == InsightType.AWARDS:
            insight_types = Insight.TYPED_LEADERBOARD_AWARD_INSIGHTS
        elif insight_type == InsightType.MATCHES:
            insight_types = Insight.TYPED_LEADERBOARD_MATCH_INSIGHTS

        overall_insights = []
        for insight_type in insight_types:
            # Skip most unique teams overall insight since we aren't tracking *which* teams are unique
            if (
                insight_type
                == Insight.TYPED_LEADERBOARD_MOST_UNIQUE_TEAMS_PLAYED_WITH_AGAINST
            ):
                continue

            insights = Insight.query(
                Insight.name == Insight.INSIGHT_NAMES[insight_type],
                Insight.year != 0,
            ).fetch(1000)

            data = defaultdict(int)
            for insight in insights:
                leaderboard_data: LeaderboardData = insight.data
                for leaderboard_ranking in leaderboard_data["rankings"]:
                    for team in leaderboard_ranking["keys"]:
                        # pyre says we can't add a possible float to an int, but it doesn't matter here
                        data[team] += leaderboard_ranking["value"]  # pyre-ignore[58]

            overall_insights.append(
                cls._create_leaderboard_from_dict_counts(
                    data,
                    insight_type,
                    year=0,
                )
            )

        return overall_insights

    @classmethod
    def _do_overall_notable_insights(cls) -> List[Insight]:
        overall_insights = []

        for insight_type in Insight.NOTABLE_INSIGHTS:
            insights = Insight.query(
                Insight.name == Insight.INSIGHT_NAMES[insight_type],
                Insight.year != 0,
            ).fetch(1000)

            team_context_map: DefaultDict[TeamKey, List[EventKey]] = defaultdict(list)
            for insight in insights:
                for entry in insight.data["entries"]:
                    team_context_map[entry["team_key"]].extend(entry["context"])

            overall_insights.append(
                cls._create_notable_insight(team_context_map, insight_type, year=0)
            )

        return overall_insights
