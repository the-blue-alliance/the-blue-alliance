import json
import logging
import math

from models.insight import Insight
from models.event import Event
from models.award import Award
from models.match import Match

from helpers.event_helper import EventHelper
from helpers.award_helper import AwardHelper

class InsightsHelper(object):
    @classmethod
    def doMatchInsights(self, year):
        insights = []
        
        events = Event.query(Event.year == year, Event.official == True).order(Event.start_date).fetch(1000)
        week_events = EventHelper.groupByWeek(events)
        
        highscore_matches_by_week = []  # tuples: week, matches
        match_averages_by_week = [] #tuples: week, average score
        elim_match_averages_by_week = []  #tuples: week, average score
        overall_match_highscore = 0
        overall_elim_match_highscore = 0
        overall_highscore_matches = []
        bucketed_scores = {}
        elim_bucketed_scores = {}
        num_matches = 0
        for week, events in week_events.items():
            week_highscore_matches = []
            week_match_highscore = 0
            week_match_sum = 0
            elim_week_match_sum = 0
            num_matches_by_week = 0
            num_elim_matches_by_week = 0
            for event in events:
                matches = event.matches
                for match in matches:
                    num_matches_by_week += 1
                    if match.comp_level in Match.ELIM_LEVELS:
                        num_elim_matches_by_week += 1
                    num_matches += 1
                    alliances = match.alliances
                    redScore = alliances['red']['score']
                    blueScore = alliances['blue']['score']

                    match_data = {'key_name': match.key_name,
                                 'verbose_name': match.verbose_name,
                                 'event_name': event.name,
                                 'alliances': alliances,
                                 'winning_alliance': match.winning_alliance
                                 }

                    # High scores grouped by week
                    if redScore >= week_match_highscore:
                        if redScore > week_match_highscore:
                            week_highscore_matches = []
                        week_highscore_matches.append(match_data)
                        week_match_highscore = redScore
                    if blueScore >= week_match_highscore:
                        if blueScore > week_match_highscore:
                            week_highscore_matches = []
                        week_highscore_matches.append(match_data)
                        week_match_highscore = blueScore
                    
                    # Overall high scores
                    if redScore >= overall_match_highscore:
                        if redScore > overall_match_highscore:
                            overall_highscore_matches = []
                        overall_highscore_matches.append(match_data)
                        overall_match_highscore = redScore
                        if match.comp_level in match.ELIM_LEVELS:
                            overall_elim_match_highscore = redScore
                    if blueScore >= overall_match_highscore:
                        if blueScore > overall_match_highscore:
                            overall_highscore_matches = []
                        overall_highscore_matches.append(match_data)
                        overall_match_highscore = blueScore
                        if match.comp_level in match.ELIM_LEVELS:
                            overall_elim_match_highscore = blueScore

                    # Bucketed scores
                    if redScore in bucketed_scores:
                        bucketed_scores[redScore] += 1
                    else:
                        bucketed_scores[redScore] = 1
                    if blueScore in bucketed_scores:
                        bucketed_scores[blueScore] += 1
                    else:
                        bucketed_scores[blueScore] = 1
                            
                    if match.comp_level in match.ELIM_LEVELS:
                        if redScore in elim_bucketed_scores:
                            elim_bucketed_scores[redScore] += 1
                        else:
                            elim_bucketed_scores[redScore] = 1
                        if blueScore in elim_bucketed_scores:
                            elim_bucketed_scores[blueScore] += 1
                        else:
                            elim_bucketed_scores[blueScore] = 1

                    # Match score sums
                    week_match_sum += redScore + blueScore
                    if match.comp_level in match.ELIM_LEVELS:
                        elim_week_match_sum += redScore + blueScore
                    
            highscore_matches_by_week.append((week, week_highscore_matches))
            
            if num_matches_by_week == 0:
                week_average = 0
            else:
                week_average = float(week_match_sum)/num_matches_by_week
            match_averages_by_week.append((week, week_average))
            
            if num_elim_matches_by_week == 0:
                week_elim_average = 0
            else:
                week_elim_average = float(elim_week_match_sum)/num_elim_matches_by_week
            elim_match_averages_by_week.append((week, week_elim_average))
          
        if overall_highscore_matches or highscore_matches_by_week:
            insights.append(Insight(
                id = Insight.renderKeyName(year, Insight.INSIGHT_NAMES[Insight.MATCH_HIGHSCORE]),
                name = Insight.INSIGHT_NAMES[Insight.MATCH_HIGHSCORE],
                year = year,
                data_json = json.dumps((overall_highscore_matches, highscore_matches_by_week))))
        
        if bucketed_scores:
            totalCount = float(sum(bucketed_scores.values()))
            bucketed_scores_normalized = {}
            binAmount = math.ceil(float(overall_match_highscore) / 20)
            for score, amount in bucketed_scores.items():
                score -= (score % binAmount) + binAmount/2
                score = int(score)
                contribution = float(amount)*100/totalCount
                if score in bucketed_scores_normalized:
                    bucketed_scores_normalized[score] += contribution
                else:
                    bucketed_scores_normalized[score] = contribution
            insights.append(Insight(
                id = Insight.renderKeyName(year, Insight.INSIGHT_NAMES[Insight.BUCKETED_SCORES]),
                name = Insight.INSIGHT_NAMES[Insight.BUCKETED_SCORES],
                year = year,
                data_json = json.dumps(bucketed_scores_normalized)))
            
        if elim_bucketed_scores:
            totalCount = float(sum(elim_bucketed_scores.values()))
            elim_bucketed_scores_normalized = {}
            # Tries to use same bucket size as bucketed_scores
            if binAmount == None:
                binAmount = math.ceil(float(overall_elim_match_highscore) / 20)
            for score, amount in elim_bucketed_scores.items():
                score -= (score % binAmount) + binAmount/2
                score = int(score)
                contribution = float(amount)*100/totalCount
                if score in elim_bucketed_scores_normalized:
                    elim_bucketed_scores_normalized[score] += contribution
                else:
                    elim_bucketed_scores_normalized[score] = contribution
            insights.append(Insight(
                id = Insight.renderKeyName(year, Insight.INSIGHT_NAMES[Insight.ELIM_BUCKETED_SCORES]),
                name = Insight.INSIGHT_NAMES[Insight.ELIM_BUCKETED_SCORES],
                year = year,
                data_json = json.dumps(elim_bucketed_scores_normalized)))
            
        if match_averages_by_week:
            insights.append(Insight(
                id = Insight.renderKeyName(year, Insight.INSIGHT_NAMES[Insight.MATCH_AVERAGES]),
                name = Insight.INSIGHT_NAMES[Insight.MATCH_AVERAGES],
                year = year,
                data_json = json.dumps(match_averages_by_week)))
            
        if elim_match_averages_by_week:
            insights.append(Insight(
                id = Insight.renderKeyName(year, Insight.INSIGHT_NAMES[Insight.ELIM_MATCH_AVERAGES]),
                name = Insight.INSIGHT_NAMES[Insight.ELIM_MATCH_AVERAGES],
                year = year,
                data_json = json.dumps(elim_match_averages_by_week)))

        if num_matches:
            insights.append(Insight(
                id = Insight.renderKeyName(year, Insight.INSIGHT_NAMES[Insight.NUM_MATCHES]),
                name = Insight.INSIGHT_NAMES[Insight.NUM_MATCHES],
                year = year,
                data_json = json.dumps(num_matches)))
            
        return insights

    @classmethod
    def doAwardInsights(self, year):
        insights = []
        
        keysToQuery = Award.BLUE_BANNER_KEYS.union(Award.DIVISION_FIN_KEYS).union(Award.CHAMPIONSHIP_FIN_KEYS)
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
            if award.name in Award.REGIONAL_WIN_KEYS:
                if teamKey in regional_winners:
                    regional_winners[teamKey] += 1
                else:
                    regional_winners[teamKey] = 1
                    
            # Division Winners
            if award.name in Award.DIVISION_WIN_KEYS:
                division_winners.append(teamKey)
                
            # Divison Finalists
            if award.name in Award.DIVISION_FIN_KEYS:
                division_finalists.append(teamKey)
                                
            # World Champions
            if award.name in Award.CHAMPIONSHIP_WIN_KEYS:
                world_champions.append(teamKey)
                
            # World Finalists
            if award.name in Award.CHAMPIONSHIP_FIN_KEYS:
                world_finalists.append(teamKey)

            # RCA Winners
            if award.name in Award.REGIONAL_CA_KEYS:
                rca_winners.append(teamKey)
                
            # CA Winner
            if award.name in Award.CHAMPIONSHIP_CA_KEYS:
                ca_winner = teamKey
            
            # Blue Banner Winners
            if award.name in Award.BLUE_BANNER_KEYS:
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
            id = Insight.renderKeyName(year, Insight.INSIGHT_NAMES[Insight.REGIONAL_DISTRICT_WINNERS]),
            name = Insight.INSIGHT_NAMES[Insight.REGIONAL_DISTRICT_WINNERS],
            year = year,
            data_json = json.dumps(regional_winners)))
        
        if division_finalists:
            insights.append(Insight(
            id = Insight.renderKeyName(year, Insight.INSIGHT_NAMES[Insight.DIVISION_FINALISTS]),
            name = Insight.INSIGHT_NAMES[Insight.DIVISION_FINALISTS],
            year = year,
            data_json = json.dumps(division_finalists)))
        
        if division_winners:
            insights.append(Insight(
            id = Insight.renderKeyName(year, Insight.INSIGHT_NAMES[Insight.DIVISION_WINNERS]),
            name = Insight.INSIGHT_NAMES[Insight.DIVISION_WINNERS],
            year = year,
            data_json = json.dumps(division_winners)))
        
        if world_finalists:
            insights.append(Insight(
            id = Insight.renderKeyName(year, Insight.INSIGHT_NAMES[Insight.WORLD_FINALISTS]),
            name = Insight.INSIGHT_NAMES[Insight.WORLD_FINALISTS],
            year = year,
            data_json = json.dumps(world_finalists)))
        
        if world_champions:
            insights.append(Insight(
            id = Insight.renderKeyName(year, Insight.INSIGHT_NAMES[Insight.WORLD_CHAMPIONS]),
            name = Insight.INSIGHT_NAMES[Insight.WORLD_CHAMPIONS],
            year = year,
            data_json = json.dumps(world_champions)))
        
        if rca_winners:
            insights.append(Insight(
            id = Insight.renderKeyName(year, Insight.INSIGHT_NAMES[Insight.RCA_WINNERS]),
            name = Insight.INSIGHT_NAMES[Insight.RCA_WINNERS],
            year = year,
            data_json = json.dumps(rca_winners)))
        
        if ca_winner:
            insights.append(Insight(
            id = Insight.renderKeyName(year, Insight.INSIGHT_NAMES[Insight.CA_WINNER]),
            name = Insight.INSIGHT_NAMES[Insight.CA_WINNER],
            year = year,
            data_json = json.dumps(ca_winner)))
        
        if blue_banners:
            insights.append(Insight(
            id = Insight.renderKeyName(year, Insight.INSIGHT_NAMES[Insight.BLUE_BANNERS]),
            name = Insight.INSIGHT_NAMES[Insight.BLUE_BANNERS],
            year = year,
            data_json = json.dumps(blue_banners)))

        return insights

    @classmethod
    def doOverallMatchInsights(self):
        insights = []
        
        year_num_matches = Insight.query(Insight.name == Insight.INSIGHT_NAMES[Insight.NUM_MATCHES], Insight.year != 0).fetch(1000)
        num_matches = []
        for insight in year_num_matches:
            num_matches.append((insight.year, insight.data))
        
        # Creating Insights
        if num_matches:
            insights.append(Insight(
            id = Insight.renderKeyName(None, Insight.INSIGHT_NAMES[Insight.NUM_MATCHES]),
            name = Insight.INSIGHT_NAMES[Insight.NUM_MATCHES],
            year = 0,
            data_json = json.dumps(num_matches)))
        
        return insights
    
    @classmethod
    def doOverallAwardInsights(self):
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
        regional_winners = sorted(regional_winners.items(), key=lambda pair: int(pair[0][3:]))   # Sort by team number
        temp = {}
        for team, numWins in regional_winners:
            if numWins in temp:
                temp[numWins] += [team]
            else:
                temp[numWins] = [team]
        regional_winners = sorted(temp.items(), key=lambda pair: int(pair[0]), reverse=True)  # Sort by win number
        
        blue_banners = sorted(blue_banners.items(), key=lambda pair: int(pair[0][3:]))   # Sort by team number
        temp = {}
        for team, numWins in blue_banners:
            if numWins in temp:
                temp[numWins].append(team)
            else:
                temp[numWins] = [team]
        blue_banners = sorted(temp.items(), key=lambda pair: int(pair[0]), reverse=True)  # Sort by banner number
        
        rca_winners = sorted(rca_winners.items(), key=lambda pair: int(pair[0][3:]))   # Sort by team number
        temp = {}
        for team, numWins in rca_winners:
            if numWins in temp:
                temp[numWins] += [team]
            else:
                temp[numWins] = [team]
        rca_winners = sorted(temp.items(), key=lambda pair: int(pair[0]), reverse=True)  # Sort by win number
        
        world_champions = sorted(world_champions.items(), key=lambda pair: int(pair[0][3:]))   # Sort by team number
        temp = {}
        for team, numWins in world_champions:
            if numWins in temp:
                temp[numWins] += [team]
            else:
                temp[numWins] = [team]
        world_champions = sorted(temp.items(), key=lambda pair: int(pair[0]), reverse=True)  # Sort by win number
        
        # Creating Insights
        if regional_winners:
            insights.append(Insight(
            id = Insight.renderKeyName(None, Insight.INSIGHT_NAMES[Insight.REGIONAL_DISTRICT_WINNERS]),
            name = Insight.INSIGHT_NAMES[Insight.REGIONAL_DISTRICT_WINNERS],
            year = 0,
            data_json = json.dumps(regional_winners)))
            
        if blue_banners:
            insights.append(Insight(
            id = Insight.renderKeyName(None, Insight.INSIGHT_NAMES[Insight.BLUE_BANNERS]),
            name = Insight.INSIGHT_NAMES[Insight.BLUE_BANNERS],
            year = 0,
            data_json = json.dumps(blue_banners)))
            
        if rca_winners:
            insights.append(Insight(
            id = Insight.renderKeyName(None, Insight.INSIGHT_NAMES[Insight.RCA_WINNERS]),
            name = Insight.INSIGHT_NAMES[Insight.RCA_WINNERS],
            year = 0,
            data_json = json.dumps(rca_winners)))
            
        if world_champions:
            insights.append(Insight(
            id = Insight.renderKeyName(None, Insight.INSIGHT_NAMES[Insight.WORLD_CHAMPIONS]),
            name = Insight.INSIGHT_NAMES[Insight.WORLD_CHAMPIONS],
            year = 0,
            data_json = json.dumps(world_champions)))
            
        return insights
