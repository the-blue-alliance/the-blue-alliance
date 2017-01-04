from google.appengine.ext import ndb

from database.database_query import DatabaseQuery
from helpers.model_to_dict import ModelToDict
from models.robot import Robot
from models.team import Team


class TeamRobotsQuery(DatabaseQuery):
    CACHE_VERSION = 0
    CACHE_KEY_FORMAT = 'team_robots_{}'  # (team_key)

    @ndb.tasklet
    def _query_async(self, dict_version):
        team_key = self._query_args[0]
        robots = yield Robot.query(
            Robot.team == ndb.Key(Team, team_key)).fetch_async()
        if dict_version:
            robots = ModelToDict.convertRobots(robots, dict_version)
        raise ndb.Return(robots)
