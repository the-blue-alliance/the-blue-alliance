from database.dict_converters.converter_base import ConverterBase


class RobotConverter(ConverterBase):
    SUBVERSIONS = {  # Increment every time a change to the dict is made
        3: 3,
    }

    @classmethod
    def _convert(cls, robots, dict_version):
        ROBOT_CONVERTERS = {
            3: cls.robotsConverter_v3,
        }
        return ROBOT_CONVERTERS[dict_version](robots)

    @classmethod
    def robotsConverter_v3(cls, robots):
        robots = map(cls.robotConverter_v3, robots)
        return robots

    @classmethod
    def robotConverter_v3(cls, robot):
        return {
            'key': robot.key_name,
            'team_key': robot.team.id(),
            'year': robot.year,
            'robot_name': robot.robot_name,
        }
