import json
import urlparse

from google.appengine.ext import ndb

from consts.district_type import DistrictType
from helpers.website_helper import WebsiteHelper
from models.district import District
from models.district_team import DistrictTeam
from models.robot import Robot
from models.team import Team
from sitevars.website_blacklist import WebsiteBlacklist


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
            team_website = teamData.get('website', None)
            # Fix issue where FIRST's API returns dummy website for all teams
            if (team_website is not None and 'www.firstinspires.org' in team_website):
                website = None
            elif WebsiteBlacklist.is_blacklisted(team_website):
                website = ''
            else:
                website = WebsiteHelper.format_url(team_website)

            team = Team(
                id="frc{}".format(teamData['teamNumber']),
                team_number=teamData['teamNumber'],
                name=teamData['nameFull'],
                nickname=teamData['nameShort'],
                school_name=teamData.get('schoolName'),
                home_cmp=teamData.get('homeCMP').lower() if teamData.get('homeCMP') else None,
                city=teamData['city'],
                state_prov=teamData['stateProv'],
                country=teamData['country'],
                website=website,
                rookie_year=teamData['rookieYear']
            )

            districtTeam = None
            if teamData['districtCode']:
                districtKey = District.renderKeyName(self.year, teamData['districtCode'].lower())
                districtTeam = DistrictTeam(
                    id=DistrictTeam.renderKeyName(districtKey, team.key_name),
                    team=ndb.Key(Team, team.key_name),
                    year=self.year,
                    district_key=ndb.Key(District, districtKey),
                )

            robot = None
            if teamData['robotName'] and self.year not in [2019]:
                # FIRST did not support entering robot names  in 2019, so the
                # data returned in the API that year is garbage. So let's not
                # import it, with the hope that it'll come back in the future
                robot = Robot(
                    id=Robot.renderKeyName(team.key_name, self.year),
                    team=ndb.Key(Team, team.key_name),
                    year=self.year,
                    robot_name=teamData['robotName'].strip()
                )

            ret_models.append((team, districtTeam, robot))

        return (ret_models, (current_page < total_pages))
