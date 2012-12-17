import json
import logging

from models.insight import Insight
from models.event import Event

from helpers.event_helper import EventHelper
from helpers.award_helper import AwardHelper

class InsightsHelper(object):
    MATCH_HIGHSCORE = 0
    MATCH_AVERAGES = 1
    BUCKETED_SCORES = 2
    REGIONAL_DISTRICT_WINNERS = 3
    DIVISION_FINALISTS = 4
    DIVISION_WINNERS = 5
    WORLD_FINALISTS = 6
    WORLD_CHAMPIONS = 7
    RCA_WINNERS = 8
    CA_WINNER = 9
    BLUE_BANNERS = 10
    
    # Used for datastore keys! Don't change unless you know what you're doing.
    INSIGHT_NAMES = {MATCH_HIGHSCORE: 'match_highscore',
                     BUCKETED_SCORES: 'bucketed_scores',
                     REGIONAL_DISTRICT_WINNERS: 'regional_district_winners',
                     DIVISION_FINALISTS: 'division_finalists',
                     DIVISION_WINNERS: 'division_winners',
                     WORLD_FINALISTS: 'world_finalists',
                     WORLD_CHAMPIONS: 'world_champions',
                     RCA_WINNERS: 'rca_winners',
                     CA_WINNER: 'ca_winner',
                     BLUE_BANNERS: 'blue_banners',
                     MATCH_AVERAGES: 'match_averages',
                     }

    @classmethod
    def doMatchInsights(self, year):
        insights = []
        
        events = Event.query(Event.year == year, Event.official == True).order(Event.start_date).fetch(1000)
        week_events = EventHelper.groupByWeek(events)
        
        highscore_matches_by_week = []  # tuples: week, matches
        match_averages_by_week = [] #tuples: week, average score
        overall_match_highscore = 0
        overall_highscore_matches = []
        bucketed_scores = {}
        for week, events in week_events.items():
            week_highscore_matches = []
            week_match_highscore = 0
            week_match_sum = 0
            num_matches = 0
            for event in events:
                matches = event.matches
                for match in matches:
                    num_matches += 1
                    alliances = match.alliances
                    redScore = alliances['red']['score']
                    blueScore = alliances['blue']['score']

                    # High scores grouped by week
                    if redScore >= week_match_highscore:
                        if redScore > week_match_highscore:
                            week_highscore_matches = []
                        week_highscore_matches.append({'key_name': match.key_name,
                                                       'verbose_name': match.verbose_name,
                                                       'event_name': event.name,
                                                       'alliances': alliances,
                                                       })
                        week_match_highscore = redScore
                    if blueScore >= week_match_highscore:
                        if blueScore > week_match_highscore:
                            week_highscore_matches = []
                        week_highscore_matches.append({'key_name': match.key_name,
                                                       'verbose_name': match.verbose_name,
                                                       'event_name': event.name,
                                                       'alliances': alliances,
                                                       })
                        week_match_highscore = blueScore
                    
                    # Overall high scores
                    if redScore >= overall_match_highscore:
                        if redScore > overall_match_highscore:
                            overall_highscore_matches = []
                        overall_highscore_matches.append({'key_name': match.key_name,
                                                          'verbose_name': match.verbose_name,
                                                          'event_name': event.name,
                                                          'alliances': alliances,
                                                          })
                        overall_match_highscore = redScore
                    if blueScore >= overall_match_highscore:
                        if blueScore > overall_match_highscore:
                            overall_highscore_matches = []
                        overall_highscore_matches.append({'key_name': match.key_name,
                                                          'verbose_name': match.verbose_name,
                                                          'event_name': event.name,
                                                          'alliances': alliances,
                                                          })
                        overall_match_highscore = blueScore
                        
                    # Bucketed scores
                    if redScore in bucketed_scores:
                        bucketed_scores[redScore] += 1
                    else:
                        bucketed_scores[redScore] = 1
                    if blueScore in bucketed_scores:
                        bucketed_scores[blueScore] += 1
                    else:
                        bucketed_scores[blueScore] = 1
                        
                    # Match score sums
                    week_match_sum += redScore + blueScore
                    
            highscore_matches_by_week.append((week, week_highscore_matches))
            match_averages_by_week.append((week, float(week_match_sum)/num_matches))
          
        if overall_highscore_matches or highscore_matches_by_week:
            insights.append(Insight(
                id = Insight.renderKeyName(year, self.INSIGHT_NAMES[self.MATCH_HIGHSCORE]),
                name = self.INSIGHT_NAMES[self.MATCH_HIGHSCORE],
                year = year,
                data_json = json.dumps((overall_highscore_matches, highscore_matches_by_week))))
        
        if bucketed_scores:
            totalCount = float(sum(bucketed_scores.values()))
            bucketed_scores_normalized = {}
            for score, amount in bucketed_scores.items():
                bucketed_scores_normalized[score] = float(amount)*100/totalCount
            insights.append(Insight(
                id = Insight.renderKeyName(year, self.INSIGHT_NAMES[self.BUCKETED_SCORES]),
                name = self.INSIGHT_NAMES[self.BUCKETED_SCORES],
                year = year,
                data_json = json.dumps(bucketed_scores_normalized)))
            
        if match_averages_by_week:
            insights.append(Insight(
                id = Insight.renderKeyName(year, self.INSIGHT_NAMES[self.MATCH_AVERAGES]),
                name = self.INSIGHT_NAMES[self.MATCH_AVERAGES],
                year = year,
                data_json = json.dumps(match_averages_by_week)))
            
        return insights

    @classmethod
    def doAwardInsights(self, year):
        insights = []
        
        keysToQuery = AwardHelper.BLUE_BANNER_KEYS.union(AwardHelper.DIVISION_FIN_KEYS).union(AwardHelper.CHAMPIONSHIP_FIN_KEYS)
        awards = AwardHelper.getAwards(keysToQuery, year)
        
        regional_winners = {}
        division_winners = []
        division_finalists = []
        world_champions = []
        world_finalists = []
        rca_winners = []
        ca_winner = None
        blue_banners = {}
        for award in awards:
            teamKey = award.team.id()

            # Regional Winners
            if award.name in AwardHelper.REGIONAL_WIN_KEYS:
                if teamKey in regional_winners:
                    regional_winners[teamKey] += 1
                else:
                    regional_winners[teamKey] = 1
                    
            # Division Winners
            if award.name in AwardHelper.DIVISION_WIN_KEYS:
                division_winners.append(teamKey)
                
            # Divison Finalists
            if award.name in AwardHelper.DIVISION_FIN_KEYS:
                division_finalists.append(teamKey)
                                
            # World Champions
            if award.name in AwardHelper.CHAMPIONSHIP_WIN_KEYS:
                world_champions.append(teamKey)
                
            # World Finalists
            if award.name in AwardHelper.CHAMPIONSHIP_FIN_KEYS:
                world_finalists.append(teamKey)

            # RCA Winners
            if award.name in AwardHelper.REGIONAL_CA_KEYS:
                rca_winners.append(teamKey)
                
            # CA Winner
            if award.name in AwardHelper.CHAMPIONSHIP_CA_KEYS:
                ca_winner = teamKey
            
            # Blue Banner Winners
            if award.name in AwardHelper.BLUE_BANNER_KEYS:
                if teamKey in blue_banners:
                    blue_banners[teamKey] += 1
                else:
                    blue_banners[teamKey] = 1
                
        # Sorting
        regional_winners = sorted(regional_winners.items(), key=lambda pair: int(pair[0][3:]))   # Sort by team number
        temp = {}
        for team, numWins in regional_winners:
            if numWins in temp:
                temp[numWins] += [team]
            else:
                temp[numWins] = [team]
        regional_winners = sorted(temp.items(), key=lambda pair: int(pair[0]), reverse=True)  # Sort by win number

        division_winners = sorted(division_winners, key=lambda team: int(team[3:]))
        division_finalists = sorted(division_finalists, key=lambda team: int(team[3:]))
        world_champions = sorted(world_champions, key=lambda team: int(team[3:]))
        world_finalists = sorted(world_finalists, key=lambda team: int(team[3:]))
        rca_winners = sorted(rca_winners, key=lambda team: int(team[3:]))
        
        blue_banners = sorted(blue_banners.items(), key=lambda pair: int(pair[0][3:]))   # Sort by team number
        temp = {}
        for team, numWins in blue_banners:
            if numWins in temp:
                temp[numWins].append(team)
            else:
                temp[numWins] = [team]
        blue_banners = sorted(temp.items(), key=lambda pair: int(pair[0]), reverse=True)  # Sort by banner number   
        
        # Creating Insights
        if regional_winners:
            insights.append(Insight(
            id = Insight.renderKeyName(year, self.INSIGHT_NAMES[self.REGIONAL_DISTRICT_WINNERS]),
            name = self.INSIGHT_NAMES[self.REGIONAL_DISTRICT_WINNERS],
            year = year,
            data_json = json.dumps(regional_winners)))
        
        if division_finalists:
            insights.append(Insight(
            id = Insight.renderKeyName(year, self.INSIGHT_NAMES[self.DIVISION_FINALISTS]),
            name = self.INSIGHT_NAMES[self.DIVISION_FINALISTS],
            year = year,
            data_json = json.dumps(division_finalists)))
        
        if division_winners:
            insights.append(Insight(
            id = Insight.renderKeyName(year, self.INSIGHT_NAMES[self.DIVISION_WINNERS]),
            name = self.INSIGHT_NAMES[self.DIVISION_WINNERS],
            year = year,
            data_json = json.dumps(division_winners)))
        
        if world_finalists:
            insights.append(Insight(
            id = Insight.renderKeyName(year, self.INSIGHT_NAMES[self.WORLD_FINALISTS]),
            name = self.INSIGHT_NAMES[self.WORLD_FINALISTS],
            year = year,
            data_json = json.dumps(world_finalists)))
        
        if world_champions:
            insights.append(Insight(
            id = Insight.renderKeyName(year, self.INSIGHT_NAMES[self.WORLD_CHAMPIONS]),
            name = self.INSIGHT_NAMES[self.WORLD_CHAMPIONS],
            year = year,
            data_json = json.dumps(world_champions)))
        
        if rca_winners:
            insights.append(Insight(
            id = Insight.renderKeyName(year, self.INSIGHT_NAMES[self.RCA_WINNERS]),
            name = self.INSIGHT_NAMES[self.RCA_WINNERS],
            year = year,
            data_json = json.dumps(rca_winners)))
        
        if ca_winner:
            insights.append(Insight(
            id = Insight.renderKeyName(year, self.INSIGHT_NAMES[self.CA_WINNER]),
            name = self.INSIGHT_NAMES[self.CA_WINNER],
            year = year,
            data_json = json.dumps(ca_winner)))
        
        if blue_banners:
            insights.append(Insight(
            id = Insight.renderKeyName(year, self.INSIGHT_NAMES[self.BLUE_BANNERS]),
            name = self.INSIGHT_NAMES[self.BLUE_BANNERS],
            year = year,
            data_json = json.dumps(blue_banners)))

        return insights
