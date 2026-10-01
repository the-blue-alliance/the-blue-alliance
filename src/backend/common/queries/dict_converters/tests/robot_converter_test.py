from google.appengine.ext import ndb

from backend.common.consts.api_version import ApiMajorVersion
from backend.common.models.robot import Robot
from backend.common.models.team import Team
from backend.common.queries.dict_converters.robot_converter import RobotConverter


def _robot() -> Robot:
    return Robot(
        id="frc254_2019",
        team=ndb.Key(Team, "frc254"),
        year=2019,
        robot_name="Backlash",
    )


def test_convert(ndb_context) -> None:
    converted = RobotConverter([_robot()]).convert(ApiMajorVersion.API_V3)
    assert converted == [
        {
            "key": "frc254_2019",
            "team_key": "frc254",
            "year": 2019,
            "robot_name": "Backlash",
        }
    ]


def test_dictToModel_v3_round_trip(ndb_context) -> None:
    robot = _robot()
    model = RobotConverter.dictToModel_v3(RobotConverter.robotConverter_v3(robot))

    assert model.key.id() == "frc254_2019"
    assert model.team == ndb.Key(Team, "frc254")
    assert model.year == 2019
    assert model.robot_name == "Backlash"
