from typing import List, Optional, Tuple

from google.appengine.ext import ndb

from backend.common.frc_api.types import SeasonTeamListModelV2, SeasonTeamModelV2
from backend.common.helpers.website_helper import WebsiteHelper
from backend.common.models.district import District
from backend.common.models.district_team import DistrictTeam
from backend.common.models.robot import Robot
from backend.common.models.team import Team
from backend.common.sitevars.website_blacklist import WebsiteBlacklist
from backend.tasks_io.datafeeds.parsers.parser_paginated import ParserPaginated


class FMSAPITeamDetailsParser(
    ParserPaginated[
        SeasonTeamListModelV2,
        List[Tuple[Team, Optional[DistrictTeam], Optional[Robot]]],
    ]
):
    def __init__(self, year: int):
        self.year = year

    def parse(
        self, response: SeasonTeamListModelV2
    ) -> Tuple[
        Optional[List[Tuple[Team, Optional[DistrictTeam], Optional[Robot]]]], bool
    ]:
        current_page = response["pageCurrent"]
        total_pages = response["pageTotal"]

        teams = []

        api_team_list: List[SeasonTeamModelV2] = response["teams"] or []
        for teamData in api_team_list:
            team_website = teamData.get("website", None)
            if team_website is None:
                website = None
            # Fix issue where FIRST's API returns dummy website for all teams
            elif "www.firstinspires.org" in team_website:
                website = None
            elif WebsiteBlacklist.is_blacklisted(team_website):
                website = ""
            else:
                website = WebsiteHelper.format_url(team_website)

            name_full = teamData["nameFull"]
            name_short = teamData["nameShort"]
            home_cmp = teamData.get("homeCMP")

            team = Team(
                id="frc{}".format(teamData["teamNumber"]),
                team_number=teamData["teamNumber"],
                # Off-season Demo Team has None as nameFull
                name=name_full.strip() if name_full else None,
                nickname=name_short.strip() if name_short else None,
                school_name=teamData.get("schoolName"),
                home_cmp=(home_cmp.lower() if home_cmp else None),
                city=teamData["city"],
                state_prov=teamData["stateProv"],
                country=teamData["country"],
                website=website,
                rookie_year=teamData["rookieYear"],
            )

            districtTeam = None
            if team_district_code := teamData["districtCode"]:
                districtKey = District.render_key_name(
                    self.year, team_district_code.lower()
                )
                districtTeam = DistrictTeam(
                    id=DistrictTeam.render_key_name(districtKey, team.key_name),
                    team=ndb.Key(Team, team.key_name),
                    year=self.year,
                    district_key=ndb.Key(District, districtKey),
                )

            robot = None
            if (robot_name := teamData["robotName"]) and self.year not in [2019]:
                # FIRST did not support entering robot names  in 2019, so the
                # data returned in the API that year is garbage. So let's not
                # import it, with the hope that it'll come back in the future
                robot = Robot(
                    id=Robot.render_key_name(team.key_name, self.year),
                    team=ndb.Key(Team, team.key_name),
                    year=self.year,
                    robot_name=robot_name.strip(),
                )

            teams.append((team, districtTeam, robot))

        return (teams if teams else None, (current_page < total_pages))
