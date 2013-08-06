import os

from google.appengine.ext.webapp import template

from controllers.base_controller import LoggedInHandler
from models.event_team import EventTeam
from models.team import Team

class AdminTeamList(LoggedInHandler):
    """
    The view of a list of teams.
    """
    def get(self):
        self._require_admin()

        teams = Team.query().order(Team.team_number)

        self.template_values.update({
            "teams": teams,
        })

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/team_list.html')
        self.response.out.write(template.render(path, self.template_values))

class AdminTeamDetail(LoggedInHandler):
    """
    The view of a single Team.
    """
    def get(self, team_number):
        self._require_admin()

        team = Team.get_by_id("frc" + team_number)
        event_teams = EventTeam.query(EventTeam.team == team.key).fetch(500)

        self.template_values.update({
            'event_teams': event_teams,
            'team': team,
        })

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/team_details.html')
        self.response.out.write(template.render(path, self.template_values))

