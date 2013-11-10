import os

from google.appengine.ext.webapp import template

from controllers.base_controller import LoggedInHandler
from models.event_team import EventTeam
from models.team import Team
from models.media import Media


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
        team_medias = Media.query(Media.references == team.key).fetch(500)

        team_media_by_year = {}
        for media in team_medias:
            if media.year in team_media_by_year:
                team_media_by_year[media.year].append(media)
            else:
                team_media_by_year[media.year] = [media]

        self.template_values.update({
            'event_teams': event_teams,
            'team': team,
            'team_media_by_year': team_media_by_year,
        })

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/team_details.html')
        self.response.out.write(template.render(path, self.template_values))
