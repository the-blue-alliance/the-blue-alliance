import os

from google.appengine.ext.webapp import template

from controllers.base_controller import LoggedInHandler
from helpers.team.team_test_creator import TeamTestCreator
from models.district_team import DistrictTeam
from models.event_team import EventTeam
from models.team import Team
from models.media import Media
from models.robot import Robot

import tba_config


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
        robots = Robot.query(Robot.team == team.key).fetch()
        district_teams = DistrictTeam.query(DistrictTeam.team == team.key).fetch()

        team_medias_by_year = {}
        for media in team_medias:
            if media.year in team_medias_by_year:
                team_medias_by_year[media.year].append(media)
            else:
                team_medias_by_year[media.year] = [media]

        self.template_values.update({
            'event_teams': event_teams,
            'team': team,
            'team_medias_by_year': team_medias_by_year,
            'robots': robots,
            'district_teams': district_teams,
        })

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/team_details.html')
        self.response.out.write(template.render(path, self.template_values))


class AdminTeamCreateTest(LoggedInHandler):
    """
    Create 6 test teams.
    """
    def get(self):
        self._require_admin()

        if tba_config.CONFIG["env"] != "prod":
            TeamTestCreator.createSixTeams()
            self.redirect("/teams/")
        else:
            logging.error("{} tried to create test teams in prod! No can do.".format(
                self.user_bundle.user.email()))
            self.redirect("/admin/")
