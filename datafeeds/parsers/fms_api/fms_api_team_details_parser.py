import datetime
import json
import logging

from google.appengine.ext import ndb

from consts.district_type import DistrictType
from models.district_team import DistrictTeam
from models.team import Team
from models.robot import Robot


class FMSAPITeamDetailsParser(object):
    def __init__(self, year, team_key):
        self.year = year
        self.team_key = team_key

    def parse(self, response):
        """
        Parse team info from FMSAPI
        Returns a tuple of models (Team, DistrictTeam, Robot)
        """

        # Get team json
        # don't need to null check, if error, HTTP code != 200, so we wont' get here
        teams = response['teams']
        teamData = teams[0]

        # concat city/state/country to get address
        address = "{}, {}, {}".format(teamData['city'], teamData['stateProv'], teamData['country'])

        team = Team(
            team_number=teamData['teamNumber'],
            name=teamData['nameFull'],
            nickname=teamData['nameShort'],
            address=address,
            rookie_year=teamData['rookieYear']
        )

        districtTeam = None
        districtAbbrev = DistrictType.abbrevs[teamData['districtCode'].lower()]
        if teamData['districtCode']:
            districtTeam = DistrictTeam(
                id=DistrictTeam.renderKeyName(self.year, districtAbbrev, team.key_name),
                team=ndb.Key(Team, team.key_name),
                year=self.year,
                district=districtAbbrev
            )

        robot = None
        if teamData['robotName']:
            robot = Robot(
                id=Robot.renderKeyName(team.key_name, self.year),
                team=ndb.Key(Team, team.key_name),
                year=self.year,
                robot_name=teamData['robotName'].strip()
            )

        return (team, districtTeam, robot)
