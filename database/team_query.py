from google.appengine.ext import ndb

from database.database_query import DatabaseQuery
from models.team import Team


class TeamListQuery(DatabaseQuery):
    CACHE_VERSION = 0
    CACHE_KEY_FORMAT = 'team_list_{}'  # (page_num)
    PAGE_SIZE = 500

    def __init__(self, page_num):
        self._query_args = (page_num, )

    @ndb.tasklet
    def _query_async(self):
        page_num = self._query_args[0]
        start = self.PAGE_SIZE * page_num
        end = start + self.PAGE_SIZE
        teams = yield Team.query(Team.team_number >= start, Team.team_number < end).fetch_async()
        raise ndb.Return(teams)
