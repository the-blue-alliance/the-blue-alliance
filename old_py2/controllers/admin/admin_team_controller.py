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
