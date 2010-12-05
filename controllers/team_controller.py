import os
import logging

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template, util

from helpers.match_helper import MatchHelper
from models import Team

# The view of a list of teams.
class TeamList(webapp.RequestHandler):
    def get(self):
        
        teams = Team.all().order('team_number').fetch(10000)
        
        template_values = {
            "teams": teams,
        }
        
        path = os.path.join(os.path.dirname(__file__), '../templates/teams/list.html')
        self.response.out.write(template.render(path, template_values))
        
# The view of a single Team.
class TeamDetail(webapp.RequestHandler):
    def get(self, team_number, year=None):
        if not year: year = 2010 #fixme: make this real. -gregmarra 17 Oct 2010
        team = Team.get_by_key_name("frc" + team_number)
        
        #todo 404 handling
                
        # First, get a list of events attended by this team in the given year.
        # We don't build this index properly yet! -gregmarra 4 Dec 2010
        events = [a.event for a in team.events]
        
        participation = list()
        
        # Return an array of event names and a list of matches from that event that the
        # team was a participant in.
        for e in events:
            match_list = e.match_set.filter("team_key_names =", team.key().name())
            matches = MatchHelper.organizeMatches(match_list)
            participation.append({ 'event' : e,
                                   'matches' : matches })
        
        template_values = { 'team' : team,
                            'participation' : participation }
        
        path = os.path.join(os.path.dirname(__file__), '../templates/teams/details.html')
        self.response.out.write(template.render(path, template_values))


