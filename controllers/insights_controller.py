import datetime
import os
import logging

from google.appengine.api import memcache
from google.appengine.ext import ndb
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

import tba_config
from base_controller import BaseHandler
from helpers.match_helper import MatchHelper
from helpers.award_helper import AwardHelper
from helpers.team_helper import TeamHelper
from helpers.event_helper import EventHelper

from models.award import Award
from models.event import Event
from models.event_team import EventTeam
from models.match import Match
from models.team import Team

VALID_YEARS = [2013, 2012, 2011, 2010, 2009, 2008, 2007]    # Only years with awards (for now)

class InsightsOverview(BaseHandler):
    """
    Show Insights Overview
    """
    def get(self):
        memcache_key = "insights_overview"
        html = memcache.get(memcache_key)
        
        if html is None:
            keysToQuery = AwardHelper.BLUE_BANNER_KEYS.union(AwardHelper.DIVISION_FIN_KEYS).union(AwardHelper.CHAMPIONSHIP_FIN_KEYS)
            awards = AwardHelper.getAwards(keysToQuery)
            
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
            regional_winners = regional_winners.items()
            regional_winners = sorted(regional_winners, key=lambda pair: int(pair[0][3:]))   # Sort by team number
            regional_winners = sorted(regional_winners, key=lambda pair: pair[1], reverse=True) # Sort by wins; sort is stable, so order from previous sort is preserved
            
            division_winners = sorted(division_winners, key=lambda team: int(team[3:]))
            division_finalists = sorted(division_finalists, key=lambda team: int(team[3:]))
            world_champions = sorted(world_champions, key=lambda team: int(team[3:]))
            world_finalists = sorted(world_finalists, key=lambda team: int(team[3:]))
            rca_winners = sorted(rca_winners, key=lambda team: int(team[3:]))
            
            blue_banners = blue_banners.items()
            blue_banners = sorted(blue_banners, key=lambda pair: int(pair[0][3:]))
            blue_banners = sorted(blue_banners, key=lambda pair: pair[1], reverse=True)            
            
            template_values = {
                'valid_years': VALID_YEARS,
                'regional_winners' : regional_winners,
                'division_winners': division_winners,
                'division_finalists': division_finalists,
                'world_champions': world_champions,
                'world_finalists': world_finalists,
                'rca_winners': rca_winners,
                'ca_winner': ca_winner,
                'blue_banners': blue_banners,
            }
        
            path = os.path.join(os.path.dirname(__file__), '../templates/insights.html')
            html = template.render(path, template_values)
            if tba_config.CONFIG["memcache"]: memcache.set(memcache_key, html, 86400) 
        
        self.response.out.write(html)

class InsightsDetail(BaseHandler):
    """
    Show Insights for a particular year
    """
    def get(self, year):
        if not year.isdigit():
            return self.redirect("/error/404")
        year = int(year)
        if year not in VALID_YEARS:
            return self.redirect("/error/404")
        
        memcache_key = "insights_detail_%s" % year
        html = memcache.get(memcache_key)
        
        if html is None:
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
            
            template_values = {
                'valid_years': VALID_YEARS,
                'selected_year': year,
                'regional_winners' : regional_winners,
                'division_winners': division_winners,
                'division_finalists': division_finalists,
                'world_champions': world_champions,
                'world_finalists': world_finalists,
                'rca_winners': rca_winners,
                'ca_winner': ca_winner,
                'blue_banners': blue_banners,
            }
        
            path = os.path.join(os.path.dirname(__file__), '../templates/insights_details.html')
            html = template.render(path, template_values)
            if tba_config.CONFIG["memcache"]: memcache.set(memcache_key, html, 86400) 
        
        self.response.out.write(html)
