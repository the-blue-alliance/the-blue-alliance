import os

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template, util

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
    def get(self, team_number, year):
        team = Team.all().filter("team_number =", int(team_number))[0]
                
        # First, get a list of events attended by this team in the given year.
        events = team.events.filter('year=', int(year))
        
        participation = []
        matches = []
        
        # Return an array of event names and a list of matches from that event that the
        # team was a participant in.
        for e in events:
            for m in e.matches:
                if team in m.teams:
                    matches.append(m)
            participation.append({ 'name' : e.name,
                                   'matches' : matches })
                                   
        template_values = { 'team' : team,
                            'participation' : participation }
        
        path = os.path.join(os.path.dirname(__file__), '../templates/teams/details.html')
        self.response.out.write(template.render(path, template_values))
        
class TeamEvents(webapp.RequestHandler):
    """
    An AJAX endpoint to return a list of a team's events given a year.
    """
    def get(self, team_number, year):
        team = Team.all().filter("team_number =", int(team_number))[0]
        events = team.events.filter("year =", int(year))
        
        path = os.path.join(os.path.dirname(__file__), '../templates/teams/teamevents.html')
        self.response.out.write(template.render(path, { 'events': events }))

class TeamMatches(webapp.RequestHandler):
    """
    An AJAX endpoint to return a list of a team's matches given an event ID.
    """
    def get(self, event_id):
        event = Event.all().get_by_id(int(event_id))[0]
        matches = event.matches
        
        path = os.path.join(os.path.dirname(__file__), '../templates/teams/teammatches.html')
        self.response.out.write(template.render(path, { 'matches': matches }))