from google.appengine.ext import ndb

from database.database_query import DatabaseQuery
from models.robot import Robot
from models.team import Team


class TeamRobotsQuery(DatabaseQuery):
    CACHE_VERSION = 0
    CACHE_KEY_FORMAT = 'team_robots_{}'  # (team_key)

    def __init__(self, team_key):
        self._query_args = (team_key, )

    @ndb.tasklet
    def _query_async(self):
        team_key = self._query_args[0]
        robots = yield Robot.query(
            Robot.team == ndb.Key(Team, team_key)).fetch_async()
        raise ndb.Return(robots)
