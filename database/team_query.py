from google.appengine.ext import ndb

from database.database_query import DatabaseQuery
from models.event import Event
from models.event_team import EventTeam
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


class EventTeamsQuery(DatabaseQuery):
    CACHE_VERSION = 0
    CACHE_KEY_FORMAT = 'event_teams_{}'  # (event_key)

    def __init__(self, event_key):
        self._query_args = (event_key, )

    @ndb.tasklet
    def _query_async(self):
        event_key = self._query_args[0]
        event_teams = yield EventTeam.query(EventTeam.event == ndb.Key(Event, event_key)).fetch_async()
        team_keys = map(lambda event_team: event_team.team, event_teams)
        teams = yield ndb.get_multi_async(team_keys)
        raise ndb.Return(teams)
