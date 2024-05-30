from typing import Any, Dict, List, Optional, Tuple

from google.appengine.ext import ndb

from backend.common.helpers.website_helper import WebsiteHelper
from backend.common.models.district import District
from backend.common.models.district_team import DistrictTeam
from backend.common.models.robot import Robot
from backend.common.models.team import Team
from backend.common.sitevars.website_blacklist import WebsiteBlacklist
from backend.tasks_io.datafeeds.parsers.json.parser_paginated_json import (
    ParserPaginatedJSON,
)


class FMSAPITeamDetailsParser(
    ParserPaginatedJSON[List[Tuple[Team, Optional[DistrictTeam], Optional[Robot]]]]
):
    def __init__(self, year: int):
        self.year = year

    def parse(
        self, response: Dict[str, Any]
    ) -> Tuple[
        Optional[List[Tuple[Team, Optional[DistrictTeam], Optional[Robot]]]], bool
    ]:
        current_page = response["pageCurrent"]
        total_pages = response["pageTotal"]

        teams = []

        for teamData in response["teams"]:
            team_website = teamData.get("website", None)
            # Fix issue where FIRST's API returns dummy website for all teams
            if team_website is not None and "www.firstinspires.org" in team_website:
                website = None
            elif WebsiteBlacklist.is_blacklisted(team_website):
                website = ""
            else:
                website = WebsiteHelper.format_url(team_website)

            team = Team(
                id="frc{}".format(teamData["teamNumber"]),
                team_number=teamData["teamNumber"],
                # Off-season Demo Team has None as nameFull
                name=teamData["nameFull"].strip() if teamData["nameFull"] else None,
                nickname=teamData["nameShort"].strip(),
                school_name=teamData.get("schoolName"),
                home_cmp=(
                    teamData.get("homeCMP").lower() if teamData.get("homeCMP") else None
                ),
                city=teamData["city"],
                state_prov=teamData["stateProv"],
                country=teamData["country"],
                website=website,
                rookie_year=teamData["rookieYear"],
            )

            districtTeam = None
            if teamData["districtCode"]:
                districtKey = District.render_key_name(
                    self.year, teamData["districtCode"].lower()
                )
                districtTeam = DistrictTeam(
                    id=DistrictTeam.render_key_name(districtKey, team.key_name),
                    team=ndb.Key(Team, team.key_name),
                    year=self.year,
                    district_key=ndb.Key(District, districtKey),
                )

            robot = None
            if teamData["robotName"] and self.year not in [2019]:
                # FIRST did not support entering robot names  in 2019, so the
                # data returned in the API that year is garbage. So let's not
                # import it, with the hope that it'll come back in the future
                robot = Robot(
                    id=Robot.render_key_name(team.key_name, self.year),
                    team=ndb.Key(Team, team.key_name),
                    year=self.year,
                    robot_name=teamData["robotName"].strip(),
                )

            teams.append((team, districtTeam, robot))

        return (teams if teams else None, (current_page < total_pages))
