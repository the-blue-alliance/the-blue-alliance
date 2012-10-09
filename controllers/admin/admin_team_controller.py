import os

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

from models.event_team import EventTeam
from models.team import Team

# The view of a list of teams.
class AdminTeamList(webapp.RequestHandler):
    def get(self):
        teams = Team.query().order(Team.team_number)
        
        template_values = {
            "teams": teams,
        }
        
        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/team_list.html')
        self.response.out.write(template.render(path, template_values))
        
# The view of a single Team.
class AdminTeamDetail(webapp.RequestHandler):
    def get(self, team_number):
        team = Team.get_by_id("frc" + team_number)
        event_teams = EventTeam.query(EventTeam.team == team.key).fetch(500)

        template_values = {
            'event_teams': event_teams,
            'team': team,
        }
        
        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/team_details.html')
        self.response.out.write(template.render(path, template_values))

