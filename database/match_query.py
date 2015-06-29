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
