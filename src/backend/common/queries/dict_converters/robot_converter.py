from typing import Dict, List

from google.cloud import ndb

from backend.common.consts.api_version import ApiMajorVersion
from backend.common.models.robot import Robot
from backend.common.models.team import Team
from backend.common.queries.dict_converters.converter_base import ConverterBase


class RobotConverter(ConverterBase):
    # SUBVERSIONS = {  # Increment every time a change to the dict is made
    #     3: 3,
    # }
    # TODO use for cache clearing

    def _convert_list(
        self, model_list: List[Robot], version: ApiMajorVersion
    ) -> List[Dict]:
        ROBOT_CONVERTERS = {
            ApiMajorVersion.API_V3: self.robotsConverter_v3,
        }
        return ROBOT_CONVERTERS[version](model_list)

    def robotsConverter_v3(self, robots: List[Robot]) -> List[Dict]:
        return list(map(self.robotConverter_v3, robots))

    def robotConverter_v3(self, robot: Robot) -> Dict:
        return {
            "key": robot.key_name,
            "team_key": robot.team.id(),
            "year": robot.year,
            "robot_name": robot.robot_name,
        }

    @staticmethod
    def dictToModel_v3(data: Dict) -> Robot:
        return Robot(
            id=data["key"],
            team=ndb.Key(Team, data["team_key"]),
            year=data["year"],
            robot_name=data["robot_name"],
        )
