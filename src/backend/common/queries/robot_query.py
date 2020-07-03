from typing import List

from google.cloud import ndb

from backend.common.models.keys import TeamKey
from backend.common.models.robot import Robot
from backend.common.models.team import Team
from backend.common.queries.database_query import DatabaseQuery
from backend.common.queries.dict_converters.robot_converter import RobotConverter


class TeamRobotsQuery(DatabaseQuery[List[Robot]]):
    DICT_CONVERTER = RobotConverter

    @ndb.tasklet
    def _query_async(self, team_key: TeamKey) -> List[Robot]:
        robots = yield Robot.query(Robot.team == ndb.Key(Team, team_key)).fetch_async()
        return robots
