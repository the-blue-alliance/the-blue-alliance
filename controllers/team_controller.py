import datetime
import os
import logging

from google.appengine.api import memcache
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template, util

from helpers.match_helper import MatchHelper
from models import EventTeam, Team

# The view of a list of teams.
class TeamList(webapp.RequestHandler):
    def get(self):
        
        memcache_key = "team_list"
        html = memcache.get(memcache_key)
        
        if html is None:
            teams = Team.all().order('team_number').fetch(10000)        
        
            template_values = {
                "teams": teams,
            }
        
            path = os.path.join(os.path.dirname(__file__), '../templates/teams/list.html')
            html = template.render(path, template_values)
            memcache.set(memcache_key, html, 3600)
        
        self.response.out.write(html)
        
# The view of a single Team.
class TeamDetail(webapp.RequestHandler):
    def get(self, team_number, year=None):
        if type(year) == str: 
            year = int(year)
            explicit_year = True
        else:
            year = datetime.datetime.now().year
            explicit_year = False
        
        memcache_key = "team_detail_%s_%s" % ("frc" + team_number, year)
        html = memcache.get(memcache_key)
        
        if html is None:
            team = Team.get_by_key_name("frc" + team_number)
            
            #todo better 404 handling
            if not team:
                self.redirect("/")
            
            events = [a.event for a in team.events if a.year == year]
            for event in events:
                if not event.start_date:
                    event.start_date = datetime.datetime(year, 12, 31) #unknown goes last
            events = sorted(events, key=lambda event: event.start_date)
            
            years = sorted(set([a.year for a in team.events if a.year != None]))
            
            participation = list()
            
            # Return an array of event names and a list of matches from that event that the
            # team was a participant in.
            for e in events:
                match_list = e.match_set.filter("team_key_names =", team.key().name())
                matches = MatchHelper.organizeMatches(match_list)
                participation.append({ 'event' : e,
                                       'matches' : matches })
            
            template_values = { "explicit_year": explicit_year,
                                "team": team,
                                "participation": participation,
                                "year": year,
                                "years": years, }
            
            path = os.path.join(os.path.dirname(__file__), '../templates/teams/details.html')
            html = template.render(path, template_values)
            memcache.set(memcache_key, html, 300)
        
        self.response.out.write(html)


