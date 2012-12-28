import json
import logging
import math

from models.insight import Insight
from models.event import Event
from models.award import Award
from models.match import Match

from helpers.event_helper import EventHelper
from helpers.event_helper import OFFSEASON_EVENTS_LABEL
from helpers.award_helper import AwardHelper

class InsightsHelper(object):
    """
    Helper for calculating insights and generating Insight objects
    """
  
    @classmethod
    def doMatchInsights(self, year):
        """
        Calculate match insights for a given year. Returns a list of Insights.
        """
        # Only fetch from DB once
        official_events = Event.query(Event.year == year).order(Event.start_date).fetch(1000)
        events_by_week = EventHelper.groupByWeek(official_events)        
        week_event_matches = []  # Tuples of: (week, events) where events are tuples of (event, matches)
        for week, events in events_by_week.items():
            if week == OFFSEASON_EVENTS_LABEL:
                continue
            week_events = []
            for event in events:
                if not event.official:
                    continue
                matches = event.matches
                week_events.append((event, matches))
            week_event_matches.append((week, week_events))
        
        insights = []
        insights += self._calculateHighscoreMatchesByWeek(week_event_matches, year)
        insights += self._calculateHighscoreMatches(week_event_matches, year)
        insights += self._calculateMatchAveragesByWeek(week_event_matches, year)
        insights += self._calculateScoreDistribution(week_event_matches, year)
        insights += self._calculateNumMatches(week_event_matches, year)
        return insights
      
    @classmethod
    def doAwardInsights(self, year):
        """
        Calculate award insights for a given year. Returns a list of Insights.
        """
        # Only fetch from DB once
        keysToQuery = Award.BLUE_BANNER_KEYS.union(Award.DIVISION_FIN_KEYS).union(Award.CHAMPIONSHIP_FIN_KEYS)
        awards = AwardHelper.getAwards(keysToQuery, year)
        
        insights = []
        insights += self._calculateBlueBanners(awards, year)
        insights += self._calculateChampionshipStats(awards, year)
        insights += self._calculateRegionalStats(awards, year)

        return insights
      
    @classmethod
    def _createInsight(self, data, name, year):
        """
        Create Insight object given data, name, and year
        """
        return Insight(id = Insight.renderKeyName(year, name),
                       name = name,
                       year = year,
                       data_json = json.dumps(data))
            
    @classmethod
    def _generateMatchData(self, match, event):
        """
        A dict of any data needed for front-end rendering
        """
        return {'key_name': match.key_name,
                'verbose_name': match.verbose_name,
                'event_name': event.name,
                'alliances': match.alliances,
                'winning_alliance': match.winning_alliance
                }
                    
    @classmethod
    def _sortTeamWinsDict(self, wins_dict):
        """
        Sorts dicts with key: number of wins, value: list of teams
        by number of wins and by team number
        """
        wins_dict = sorted(wins_dict.items(), key=lambda pair: int(pair[0][3:]))   # Sort by team number
        temp = {}
        for team, numWins in wins_dict:
            if numWins in temp:
                temp[numWins] += [team]
            else:
                temp[numWins] = [team]
        return sorted(temp.items(), key=lambda pair: int(pair[0]), reverse=True)  # Sort by win number

    @classmethod
    def _sortTeamList(self, team_list):
        """
        Sorts list of teams
        """
        return sorted(team_list, key=lambda team: int(team[3:]))   # Sort by team number
      
    @classmethod
    def _calculateHighscoreMatchesByWeek(self, week_event_matches, year):
        """
        Returns an Insight where the data is a list of tuples:
        (week string, list of highest scoring matches)
        """
        highscore_matches_by_week = []  # tuples: week, list of matches (if there are ties)
        for week, week_events in week_event_matches:
            week_highscore_matches = []
            highscore = 0
            for event, matches in week_events:
                for match in matches:
                    redScore = int(match.alliances['red']['score'])
                    blueScore = int(match.alliances['blue']['score'])
                    maxScore = max(redScore, blueScore)
                    if maxScore >= highscore:
                        if maxScore > highscore:
                            week_highscore_matches = []
                        week_highscore_matches.append(self._generateMatchData(match, event))
                        highscore = maxScore
            highscore_matches_by_week.append((week, week_highscore_matches))

        insight = None
        if highscore_matches_by_week != []:
            insight = self._createInsight(highscore_matches_by_week, Insight.INSIGHT_NAMES[Insight.MATCH_HIGHSCORE_BY_WEEK], year)
        if insight != None:
            return [insight]
        else:
            return []
          
    @classmethod
    def _calculateHighscoreMatches(self, week_event_matches, year):
        """
        Returns an Insight where the data is list of highest scoring matches
        """
        highscore_matches = []  #list of matches (if there are ties)
        highscore = 0
        for _, week_events in week_event_matches:
            for event, matches in week_events:
                for match in matches:
                    redScore = int(match.alliances['red']['score'])
                    blueScore = int(match.alliances['blue']['score'])
                    maxScore = max(redScore, blueScore)
                    if maxScore >= highscore:
                        if maxScore > highscore:
                            highscore_matches = []
                        highscore_matches.append(self._generateMatchData(match, event))
                        highscore = maxScore

        insight = None
        if highscore_matches != []:
            insight = self._createInsight(highscore_matches, Insight.INSIGHT_NAMES[Insight.MATCH_HIGHSCORE], year)
        if insight != None:
            return [insight]
        else:
            return []

    @classmethod
    def _calculateMatchAveragesByWeek(self, week_event_matches, year):
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
                    redScore = int(match.alliances['red']['score'])
                    blueScore = int(match.alliances['blue']['score'])
                    week_match_sum += redScore + blueScore
                    num_matches_by_week += 1
                    if match.comp_level in Match.ELIM_LEVELS:
                        elim_week_match_sum += redScore + blueScore
                        elim_num_matches_by_week += 1
                
            if num_matches_by_week == 0:
                week_average = 0
            else:
                week_average = float(week_match_sum)/num_matches_by_week
            match_averages_by_week.append((week, week_average))
            
            if elim_num_matches_by_week == 0:
                elim_week_average = 0
            else:
                elim_week_average = float(elim_week_match_sum)/elim_num_matches_by_week
            elim_match_averages_by_week.append((week, elim_week_average))
            
        insights = []
        if match_averages_by_week != []:
            insights.append(self._createInsight(match_averages_by_week, Insight.INSIGHT_NAMES[Insight.MATCH_AVERAGES_BY_WEEK], year))
        if elim_match_averages_by_week != []:
            insights.append(self._createInsight(elim_match_averages_by_week, Insight.INSIGHT_NAMES[Insight.ELIM_MATCH_AVERAGES_BY_WEEK], year))
        return insights
          
    @classmethod
    def _calculateScoreDistribution(self, week_event_matches, year):
        """
        Returns a list of Insights, one for all data and one for elim data
        The data for each Insight is a dict:
        Key: Middle score of a bucketed range of scores, Value: % occurrence
        """
        score_distribution = {}
        elim_score_distribution = {}
        overall_highscore = 0
        for _, week_events in week_event_matches:
            for _, matches in week_events:
                for match in matches:
                    redScore = int(match.alliances['red']['score'])
                    blueScore = int(match.alliances['blue']['score'])
                    
                    overall_highscore = max(overall_highscore, redScore, blueScore)
                    
                    if redScore in score_distribution:
                        score_distribution[redScore] += 1
                    else:
                        score_distribution[redScore] = 1
                    if blueScore in score_distribution:
                        score_distribution[blueScore] += 1
                    else:
                        score_distribution[blueScore] = 1
                    
                    if match.comp_level in Match.ELIM_LEVELS:
                        if redScore in elim_score_distribution:
                            elim_score_distribution[redScore] += 1
                        else:
                            elim_score_distribution[redScore] = 1
                        if blueScore in elim_score_distribution:
                            elim_score_distribution[blueScore] += 1
                        else:
                            elim_score_distribution[blueScore] = 1
                      
        insights = []
        if score_distribution != {}:
            binAmount = math.ceil(float(overall_highscore) / 20)
            totalCount = float(sum(score_distribution.values()))
            score_distribution_normalized = {}
            for score, amount in score_distribution.items():
                roundedScore = score - int((score % binAmount) + binAmount/2)
                contribution = float(amount)*100/totalCount
                if roundedScore in score_distribution_normalized:
                    score_distribution_normalized[roundedScore] += contribution
                else:
                    score_distribution_normalized[roundedScore] = contribution
            insights.append(self._createInsight(score_distribution_normalized, Insight.INSIGHT_NAMES[Insight.SCORE_DISTRIBUTION], year))
        if elim_score_distribution != {}:
            if binAmount == None: # Use same binAmount from above if possible
                binAmount = math.ceil(float(overall_highscore) / 20)
            totalCount = float(sum(elim_score_distribution.values()))
            elim_score_distribution_normalized = {}
            for score, amount in elim_score_distribution.items():
                roundedScore = score - int((score % binAmount) + binAmount/2)
                contribution = float(amount)*100/totalCount
                if roundedScore in elim_score_distribution_normalized:
                    elim_score_distribution_normalized[roundedScore] += contribution
                else:
                    elim_score_distribution_normalized[roundedScore] = contribution
            insights.append(self._createInsight(elim_score_distribution_normalized, Insight.INSIGHT_NAMES[Insight.ELIM_SCORE_DISTRIBUTION], year))
                      
        return insights
      
    @classmethod
    def _calculateNumMatches(self, week_event_matches, year):
        """
        Returns an Insight where the data is the number of matches
        """
        numMatches = 0
        for _, week_events in week_event_matches:
            for _, matches in week_events:
                numMatches += len(matches)
            
        insight = None
        if numMatches != 0:
            insight = self._createInsight(numMatches, Insight.INSIGHT_NAMES[Insight.NUM_MATCHES], year)
        if insight != None:
            return [insight]
        else:
            return []

    @classmethod
    def _calculateBlueBanners(self, awards, year):
        """
        Returns an Insight where the data is a dict:
        Key: number of blue banners, Value: list of teams with that number of blue banners
        """
        blue_banner_winners = {}
        for award in awards:
            if award.name in Award.BLUE_BANNER_KEYS:
                teamKey = award.team.id()
                if teamKey in blue_banner_winners:
                    blue_banner_winners[teamKey] += 1
                else:
                    blue_banner_winners[teamKey] = 1
        blue_banner_winners = self._sortTeamWinsDict(blue_banner_winners)
        
        insight = None
        if blue_banner_winners != []:
            insight = self._createInsight(blue_banner_winners, Insight.INSIGHT_NAMES[Insight.BLUE_BANNERS], year)
        if insight != None:
            return [insight]
        else:
            return []

    @classmethod
    def _calculateChampionshipStats(self, awards, year):
        """
        Returns a list of Insights where, depending on the Insight, the data
        is either a team or a list of teams
        """
        ca_winner = None
        world_champions = []
        world_finalists = []
        division_winners = []
        division_finalists = []
        for award in awards:
            teamKey = award.team.id()
            if award.name in Award.CHAMPIONSHIP_CA_KEYS:
                ca_winner = teamKey
            if award.name in Award.CHAMPIONSHIP_WIN_KEYS:
                world_champions.append(teamKey)
            if award.name in Award.CHAMPIONSHIP_FIN_KEYS:
                world_finalists.append(teamKey)
            if award.name in Award.DIVISION_WIN_KEYS:
                division_winners.append(teamKey)
            if award.name in Award.DIVISION_FIN_KEYS:
                division_finalists.append(teamKey)
                
        world_champions = self._sortTeamList(world_champions)
        world_finalists = self._sortTeamList(world_finalists)
        division_winners = self._sortTeamList(division_winners)
        division_finalists = self._sortTeamList(division_finalists)

        insights = []
        if ca_winner != None:
            insights += [self._createInsight(ca_winner, Insight.INSIGHT_NAMES[Insight.CA_WINNER], year)]
        if world_champions != []:
            insights += [self._createInsight(world_champions, Insight.INSIGHT_NAMES[Insight.WORLD_CHAMPIONS], year)]
        if world_finalists != []:
            insights += [self._createInsight(world_finalists, Insight.INSIGHT_NAMES[Insight.WORLD_FINALISTS], year)]
        if division_winners != []:
            insights += [self._createInsight(division_winners, Insight.INSIGHT_NAMES[Insight.DIVISION_WINNERS], year)]
        if division_finalists != []:
            insights += [self._createInsight(division_finalists, Insight.INSIGHT_NAMES[Insight.DIVISION_FINALISTS], year)]
        return insights
      
    @classmethod
    def _calculateRegionalStats(self, awards, year):
        """
        Returns a list of Insights where, depending on the Insight, the data
        is either a list of teams or a dict:
        Key: number of wins, Value: list of teams with that number of wins
        """
        rca_winners = []
        regional_winners = {}
        for award in awards:
            teamKey = award.team.id()
            if award.name in Award.REGIONAL_CA_KEYS:
                rca_winners.append(teamKey)
            if award.name in Award.REGIONAL_WIN_KEYS:
                if teamKey in regional_winners:
                    regional_winners[teamKey] += 1
                else:
                    regional_winners[teamKey] = 1
        
        rca_winners = self._sortTeamList(rca_winners)
        regional_winners = self._sortTeamWinsDict(regional_winners)
        
        insights = []
        if rca_winners != []:
            insights += [self._createInsight(rca_winners, Insight.INSIGHT_NAMES[Insight.RCA_WINNERS], year)]
        if regional_winners != []:
            insights += [self._createInsight(regional_winners, Insight.INSIGHT_NAMES[Insight.REGIONAL_DISTRICT_WINNERS], year)]
        return insights
      
    @classmethod
    def doOverallMatchInsights(self):
        """
        Calculate match insights across all years. Returns a list of Insights.
        """
        insights = []
        
        year_num_matches = Insight.query(Insight.name == Insight.INSIGHT_NAMES[Insight.NUM_MATCHES], Insight.year != 0).fetch(1000)
        num_matches = []
        for insight in year_num_matches:
            num_matches.append((insight.year, insight.data))
        
        # Creating Insights
        if num_matches:
            insights.append(self._createInsight(num_matches, Insight.INSIGHT_NAMES[Insight.NUM_MATCHES], 0))
        
        return insights
    
    @classmethod
    def doOverallAwardInsights(self):
        """
        Calculate award insights across all years. Returns a list of Insights.
        """
        insights = []
        
        year_regional_winners = Insight.query(Insight.name == Insight.INSIGHT_NAMES[Insight.REGIONAL_DISTRICT_WINNERS], Insight.year != 0).fetch(1000)
        regional_winners = {}
        for insight in year_regional_winners:
            for number, team_list in insight.data:
                for team in team_list:
                    if team in regional_winners:
                        regional_winners[team] += number
                    else:
                        regional_winners[team] = number
        
        year_blue_banners = Insight.query(Insight.name == Insight.INSIGHT_NAMES[Insight.BLUE_BANNERS], Insight.year != 0).fetch(1000)
        blue_banners = {}
        for insight in year_blue_banners:
            for number, team_list in insight.data:
                for team in team_list:
                    if team in blue_banners:
                        blue_banners[team] += number
                    else:
                        blue_banners[team] = number
                        
        year_rca_winners = Insight.query(Insight.name == Insight.INSIGHT_NAMES[Insight.RCA_WINNERS], Insight.year != 0).fetch(1000)
        rca_winners = {}
        for insight in year_rca_winners:
            for team in insight.data:
                if team in rca_winners:
                    rca_winners[team] += 1
                else:
                    rca_winners[team] = 1
                    
        year_world_champions = Insight.query(Insight.name == Insight.INSIGHT_NAMES[Insight.WORLD_CHAMPIONS], Insight.year != 0).fetch(1000)
        world_champions = {}
        for insight in year_world_champions:
            for team in insight.data:
                if team in world_champions:
                    world_champions[team] += 1
                else:
                    world_champions[team] = 1
        
        # Sorting
        regional_winners = self._sortTeamWinsDict(regional_winners)
        blue_banners = self._sortTeamWinsDict(blue_banners)
        rca_winners = self._sortTeamWinsDict(rca_winners)
        world_champions = self._sortTeamWinsDict(world_champions)
        
        # Creating Insights
        if regional_winners:
            insights.append(self._createInsight(regional_winners, Insight.INSIGHT_NAMES[Insight.REGIONAL_DISTRICT_WINNERS], 0))
            
        if blue_banners:
            insights.append(self._createInsight(blue_banners, Insight.INSIGHT_NAMES[Insight.BLUE_BANNERS], 0))
            
        if rca_winners:
            insights.append(self._createInsight(rca_winners, Insight.INSIGHT_NAMES[Insight.RCA_WINNERS], 0))
            
        if world_champions:
            insights.append(self._createInsight(world_champions, Insight.INSIGHT_NAMES[Insight.WORLD_CHAMPIONS], 0))
            
        return insights
