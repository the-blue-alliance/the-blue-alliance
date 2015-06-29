from google.appengine.ext import ndb

from database.database_query import DatabaseQuery
from models.award import Award
from models.event import Event


class EventAwardsQuery(DatabaseQuery):
    CACHE_VERSION = 0
    CACHE_KEY_FORMAT = 'event_awards_{}'  # (event_key)

    def __init__(self, event_key):
        self._query_args = (event_key, )

    @ndb.tasklet
    def _query_async(self):
        event_key = self._query_args[0]
        awards = yield Award.query(Award.event == ndb.Key(Event, event_key)).fetch_async()
        raise ndb.Return(awards)
