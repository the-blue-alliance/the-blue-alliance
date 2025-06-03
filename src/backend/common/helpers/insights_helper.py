import itertools
import math
from collections import defaultdict
from typing import Dict, List, NamedTuple

import numpy as np
from google.appengine.ext import ndb
from pyre_extensions import none_throws

from backend.common.consts.alliance_color import AllianceColor
from backend.common.consts.award_type import BLUE_BANNER_AWARDS, AwardType
from backend.common.consts.comp_level import ELIM_LEVELS, CompLevel
from backend.common.consts.event_type import (CMP_EVENT_TYPES,
                                              SEASON_EVENT_TYPES, EventType)
from backend.common.futures import TypedFuture
from backend.common.helpers.event_helper import (OFFSEASON_EVENTS_LABEL,
                                                 PRESEASON_EVENTS_LABEL,
                                                 EventHelper)
from backend.common.helpers.event_insights_helper import EventInsightsHelper
from backend.common.helpers.insights_helper_utils import (create_insight,
                                                          sort_counter_dict)
from backend.common.models.award import Award
from backend.common.models.event import Event
from backend.common.models.insight import Insight
from backend.common.models.keys import Year
from backend.common.models.match import Match
from backend.common.models.team import Team


class EventMatches(NamedTuple):
    event: Event
    matches: List[Match]


class WeekEventMatches(NamedTuple):
    week: str
    event_matches: List[EventMatches]


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
        insights += self._calculateSuccessfulElimTeamups(
            award_futures, year, isEinstein=True
        )

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
            create_insight(data, Insight.INSIGHT_NAMES[Insight.MATCH_PREDICTIONS], year)
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
            insight = create_insight(
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
            insight = create_insight(
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

        grouped_by_win_count = sort_counter_dict(counter)

        return [
            create_insight(
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
                create_insight(
                    match_averages_by_week,
                    Insight.INSIGHT_NAMES[Insight.MATCH_AVERAGES_BY_WEEK],
                    year,
                )
            )
        if elim_match_averages_by_week != []:
            insights.append(
                create_insight(
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
                create_insight(
                    match_average_margins_by_week,
                    Insight.INSIGHT_NAMES[Insight.MATCH_AVERAGE_MARGINS_BY_WEEK],
                    year,
                )
            )
        if elim_match_average_margins_by_week != []:
            insights.append(
                create_insight(
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
                create_insight(
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
                create_insight(
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
                create_insight(
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
                    elim_winning_margin_distribution_normalized[roundedScore] += contribution
                else:
                    elim_winning_margin_distribution_normalized[roundedScore] = (
                        contribution
                    )

            insights.append(
                create_insight(
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
            create_insight(numMatches, Insight.INSIGHT_NAMES[Insight.NUM_MATCHES], year)
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
                create_insight(
                    event_insights_by_week,
                    Insight.INSIGHT_NAMES[Insight.YEAR_SPECIFIC_BY_WEEK],
                    year,
                )
            )
        if total_insights:
            insights.append(
                create_insight(
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
        blue_banner_winners = sort_counter_dict(blue_banner_winners)

        insight = None
        if blue_banner_winners != []:
            insight = create_insight(
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
                create_insight(
                    ca_winner, Insight.INSIGHT_NAMES[Insight.CA_WINNER], year
                )
            ]
        if world_champions != []:
            insights += [
                create_insight(
                    world_champions,
                    Insight.INSIGHT_NAMES[Insight.WORLD_CHAMPIONS],
                    year,
                )
            ]
        if world_finalists != []:
            insights += [
                create_insight(
                    world_finalists,
                    Insight.INSIGHT_NAMES[Insight.WORLD_FINALISTS],
                    year,
                )
            ]
        if division_winners != []:
            insights += [
                create_insight(
                    division_winners,
                    Insight.INSIGHT_NAMES[Insight.DIVISION_WINNERS],
                    year,
                )
            ]
        if division_finalists != []:
            insights += [
                create_insight(
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
        regional_winners = sort_counter_dict(regional_winners)

        insights = []
        if rca_winners != []:
            insights += [
                create_insight(
                    rca_winners, Insight.INSIGHT_NAMES[Insight.RCA_WINNERS], year
                )
            ]
        if regional_winners != []:
            insights += [
                create_insight(
                    regional_winners,
                    Insight.INSIGHT_NAMES[Insight.REGIONAL_DISTRICT_WINNERS],
                    year,
                )
            ]
        return insights

    @classmethod
    def _calculateSuccessfulElimTeamups(
        self,
        award_futures: List[TypedFuture[Award]],
        year: Year,
        isEinstein: bool = False,
    ) -> List[Insight]:
        """
        Returns an Insight where the data is a list of list of teams that won an event together
        """
        successful_elim_teamups = []
        for award_future in award_futures:
            award = award_future.get_result()
            if award.award_type_enum == AwardType.WINNER and (
                not isEinstein or award.event_type_enum == EventType.CMP_FINALS
            ):
                successful_elim_teamups.append(
                    [team_key.id() for team_key in award.team_list]
                )

        if successful_elim_teamups != []:
            return [
                create_insight(
                    successful_elim_teamups,
                    Insight.INSIGHT_NAMES[
                        (
                            Insight.SUCCESSFUL_EINSTEIN_TEAMUPS
                            if isEinstein
                            else Insight.SUCCESSFUL_ELIM_TEAMUPS
                        )
                    ],
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
                create_insight(
                    num_matches, Insight.INSIGHT_NAMES[Insight.NUM_MATCHES], 0
                )
            )

        return insights

    @classmethod
    def _calculate_einstein_streaks(cls, division_winners_map: Dict[str, List[int]]) -> Dict[str, int]:
        from collections import defaultdict  # Ensure defaultdict is available

        einstein_streak_output = defaultdict(int)
        for team_key, unsorted_years_list in division_winners_map.items():
            years = sorted(unsorted_years_list)

            if not years:
                einstein_streak_output[team_key] = 0
                continue

            # Initialize streaks
            # Every team with at least one year has a max streak of at least 1
            max_streak_for_team = 1
            current_streak = 1
            last_year_in_streak = years[0]

            # Iterate starting from the second year
            for i in range(1, len(years)):
                current_year = years[i]
                # A streak continues if current_year is last_year_in_streak + 1
                # OR if last_year_in_streak was 2019 and current_year is 2022 (COVID gap)
                is_consecutive = (current_year == last_year_in_streak + 1) or \
                                 (last_year_in_streak == 2019 and current_year == 2022)

                if is_consecutive:
                    current_streak += 1
                else:
                    # Streak broken, current_streak for the new potential streak starts at 1
                    current_streak = 1

                if current_streak > max_streak_for_team:
                    max_streak_for_team = current_streak

                last_year_in_streak = current_year

            einstein_streak_output[team_key] = max_streak_for_team

        return dict(einstein_streak_output)

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

        einstein_streak = self._calculate_einstein_streaks(division_winners)

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

        year_successful_einstein_teamups = Insight.query(
            Insight.name == Insight.INSIGHT_NAMES[Insight.SUCCESSFUL_EINSTEIN_TEAMUPS],
            Insight.year != 0,
        ).fetch(1000)
        successful_einstein_teamups = defaultdict(int)
        for insight in year_successful_einstein_teamups:
            for teams in insight.data:
                for pairs in itertools.combinations(teams, 2):
                    successful_einstein_teamups[tuple(sorted(pairs))] += 1
        successful_einstein_teamups_sorted = defaultdict(list)
        for teams, num_wins in successful_einstein_teamups.items():
            sorted_teams = sorted(teams, key=lambda team_key: int(team_key[3:]))
            successful_einstein_teamups_sorted[num_wins].append(sorted_teams)
        successful_einstein_teamups_sorted = sorted(
            successful_einstein_teamups_sorted.items(), key=lambda x: -x[0]
        )

        # Sorting
        regional_winners = sort_counter_dict(regional_winners)
        blue_banners = sort_counter_dict(blue_banners)
        rca_winners = sort_counter_dict(rca_winners)
        world_champions = self._sortTeamYearWinsDict(world_champions)
        division_winners = self._sortTeamYearWinsDict(division_winners)
        einstein_streak = sort_counter_dict(einstein_streak)

        # Creating Insights
        if regional_winners:
            insights.append(
                create_insight(
                    regional_winners,
                    Insight.INSIGHT_NAMES[Insight.REGIONAL_DISTRICT_WINNERS],
                    0,
                )
            )

        if blue_banners:
            insights.append(
                create_insight(
                    blue_banners, Insight.INSIGHT_NAMES[Insight.BLUE_BANNERS], 0
                )
            )

        if rca_winners:
            insights.append(
                create_insight(
                    rca_winners, Insight.INSIGHT_NAMES[Insight.RCA_WINNERS], 0
                )
            )

        if world_champions:
            insights.append(
                create_insight(
                    world_champions, Insight.INSIGHT_NAMES[Insight.WORLD_CHAMPIONS], 0
                )
            )

        if division_winners:
            insights.append(
                create_insight(
                    division_winners, Insight.INSIGHT_NAMES[Insight.DIVISION_WINNERS], 0
                )
            )

        if einstein_streak:
            insights.append(
                create_insight(
                    einstein_streak, Insight.INSIGHT_NAMES[Insight.EINSTEIN_STREAK], 0
                )
            )

        if year_successful_elim_teamups:
            insights.append(
                create_insight(
                    successful_elim_teamups_sorted,
                    Insight.INSIGHT_NAMES[Insight.SUCCESSFUL_ELIM_TEAMUPS],
                    0,
                )
            )

        if year_successful_einstein_teamups:
            insights.append(
                create_insight(
                    successful_einstein_teamups_sorted,
                    Insight.INSIGHT_NAMES[Insight.SUCCESSFUL_EINSTEIN_TEAMUPS],
                    0,
                )
            )

        return insights
