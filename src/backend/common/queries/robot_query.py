from typing import Any, Generator, List

from google.appengine.ext import ndb

from backend.common.models.keys import TeamKey
from backend.common.models.robot import Robot
from backend.common.models.team import Team
from backend.common.queries.database_query import CachedDatabaseQuery
from backend.common.queries.dict_converters.robot_converter import (
    RobotConverter,
    RobotDict,
)
from backend.common.tasklets import typed_tasklet


class TeamRobotsQuery(CachedDatabaseQuery[List[Robot], List[RobotDict]]):
    CACHE_VERSION = 0
    CACHE_KEY_FORMAT = "team_robots_{team_key}"
    DICT_CONVERTER = RobotConverter

    def __init__(self, team_key: TeamKey) -> None:
        super().__init__(team_key=team_key)

    @typed_tasklet
    def _query_async(self, team_key: TeamKey) -> Generator[Any, Any, List[Robot]]:
        robots = yield Robot.query(Robot.team == ndb.Key(Team, team_key)).fetch_async()
        return robots
