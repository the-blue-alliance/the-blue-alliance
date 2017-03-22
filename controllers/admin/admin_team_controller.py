import os

from google.appengine.ext import ndb
from google.appengine.ext.webapp import template

from controllers.base_controller import LoggedInHandler
from database.team_query import TeamParticipationQuery
from helpers.robot_manipulator import RobotManipulator
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
        if not team:
            self.abort(404)
        event_teams = EventTeam.query(EventTeam.team == team.key).fetch(500)
        team_medias = Media.query(Media.references == team.key).fetch(500)
        robots = Robot.query(Robot.team == team.key).fetch()
        district_teams = DistrictTeam.query(DistrictTeam.team == team.key).fetch()
        years_participated = sorted(TeamParticipationQuery(team.key_name).fetch())

        team_medias_by_year = {}
        for media in team_medias:
            if media.year in team_medias_by_year:
                team_medias_by_year[media.year].append(media)
            else:
                team_medias_by_year[media.year] = [media]
        media_years = sorted(team_medias_by_year.keys())

        self.template_values.update({
            'event_teams': event_teams,
            'team': team,
            'team_media_years': media_years,
            'team_medias_by_year': team_medias_by_year,
            'robots': robots,
            'district_teams': district_teams,
            'years_participated': years_participated,
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


class AdminTeamRobotNameUpdate(LoggedInHandler):
    """
    Updates a robot name for a given team + year
    """
    def post(self):
        self._require_admin()

        team_key = self.request.get('team_key')
        year = int(self.request.get('robot_year'))
        name = self.request.get('robot_name')

        team = Team.get_by_id(team_key)
        if not team:
            self.abort(404)

        if not year or not name:
            self.abort(400)

        robot = Robot(
            id=Robot.renderKeyName(team_key, year),
            team=team.key,
            year=year,
            robot_name=name.strip()
        )
        RobotManipulator.createOrUpdate(robot)
        self.redirect('/admin/team/{}'.format(team.team_number))
