from google.appengine.ext import ndb

from database.database_query import DatabaseQuery
from models.event import Event
from models.match import Match


class EventMatchesQuery(DatabaseQuery):
    CACHE_VERSION = 0
    CACHE_KEY_FORMAT = 'event_matches_{}'  # (event_key)

    def __init__(self, event_key):
        self._query_args = (event_key, )

    @ndb.tasklet
    def _query_async(self):
        event_key = self._query_args[0]
        matches = yield Match.query(Match.event == ndb.Key(Event, event_key)).fetch_async()
        raise ndb.Return(matches)


class TeamEventMatchesQuery(DatabaseQuery):
    CACHE_VERSION = 0
    CACHE_KEY_FORMAT = 'team_event_matches_{}_{}'  # (team_key, event_key)

    def __init__(self, team_key, event_key):
        self._query_args = (team_key, event_key, )

    @ndb.tasklet
    def _query_async(self):
        team_key = self._query_args[0]
        event_key = self._query_args[1]
        matches = yield Match.query(
            Match.team_key_names == team_key,
            Match.event == ndb.Key(Event, event_key)).fetch_async()
        raise ndb.Return(matches)
