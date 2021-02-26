from typing import Dict, List, NewType

from google.cloud import ndb

from backend.common.consts.api_version import ApiMajorVersion
from backend.common.models.robot import Robot
from backend.common.models.team import Team
from backend.common.queries.dict_converters.converter_base import ConverterBase

RobotDict = NewType("RobotDict", Dict)


class RobotConverter(ConverterBase):
    SUBVERSIONS = {  # Increment every time a change to the dict is made
        ApiMajorVersion.API_V3: 3,
    }

    @classmethod
    def _convert_list(
        cls, model_list: List[Robot], version: ApiMajorVersion
    ) -> List[RobotDict]:
        ROBOT_CONVERTERS = {
            ApiMajorVersion.API_V3: cls.robotsConverter_v3,
        }
        return ROBOT_CONVERTERS[version](model_list)

    @classmethod
    def robotsConverter_v3(cls, robots: List[Robot]) -> List[RobotDict]:
        return list(map(cls.robotConverter_v3, robots))

    @classmethod
    def robotConverter_v3(cls, robot: Robot) -> RobotDict:
        return RobotDict(
            {
                "key": robot.key_name,
                "team_key": robot.team.id(),
                "year": robot.year,
                "robot_name": robot.robot_name,
            }
        )

    @staticmethod
    def dictToModel_v3(data: Dict) -> Robot:
        return Robot(
            id=data["key"],
            team=ndb.Key(Team, data["team_key"]),
            year=data["year"],
            robot_name=data["robot_name"],
        )
