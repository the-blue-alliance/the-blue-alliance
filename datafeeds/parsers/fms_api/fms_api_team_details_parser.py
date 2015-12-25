from google.appengine.ext import ndb

from consts.district_type import DistrictType
from models.district_team import DistrictTeam
from models.team import Team
from models.robot import Robot


class FMSAPITeamDetailsParser(object):
    def __init__(self, year):
        self.year = year

    def parse(self, response):
        """
        Parse team info from FMSAPI
        Returns a tuple of: list of models (Team, DistrictTeam, Robot),
        and a Boolean indicating if there are more pages to be fetched
        """

        # Get team json
        # don't need to null check, if error, HTTP code != 200, so we wont' get here
        current_page = response['pageCurrent']
        total_pages = response['pageTotal']
        teams = response['teams']
        ret_models = []

        for teamData in teams:
            # concat city/state/country to get address
            address = u"{}, {}, {}".format(teamData['city'], teamData['stateProv'], teamData['country'])

            team = Team(
                id="frc{}".format(teamData['teamNumber']),
                team_number=teamData['teamNumber'],
                name=teamData['nameFull'],
                nickname=teamData['nameShort'],
                address=address,
                website=teamData['website'],
                rookie_year=teamData['rookieYear']
            )

            districtTeam = None
            if teamData['districtCode']:
                districtAbbrev = DistrictType.abbrevs[teamData['districtCode'].lower()]
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

            ret_models.append((team, districtTeam, robot))

        return (ret_models, (current_page < total_pages))
