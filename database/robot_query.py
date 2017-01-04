from google.appengine.ext import ndb

from database.database_query import DatabaseQuery
from database.dict_converters.robot_converter import RobotConverter
from models.robot import Robot
from models.team import Team


class TeamRobotsQuery(DatabaseQuery):
    CACHE_VERSION = 0
    CACHE_KEY_FORMAT = 'team_robots_{}'  # (team_key)
    DICT_CONVERTER = RobotConverter

    @ndb.tasklet
    def _query_async(self):
        team_key = self._query_args[0]
        robots = yield Robot.query(
            Robot.team == ndb.Key(Team, team_key)).fetch_async()
        raise ndb.Return(robots)
