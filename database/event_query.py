from google.appengine.ext import ndb

from database.database_query import DatabaseQuery
from models.event import Event


class EventListQuery(DatabaseQuery):
    CACHE_VERSION = 0
    CACHE_KEY_FORMAT = 'event_list_{}'  # (year)

    def __init__(self, year):
        self._query_args = (year, )

    @ndb.tasklet
    def _query_async(self):
        year = self._query_args[0]
        events = yield Event.query(Event.year == year).fetch_async()
        raise ndb.Return(events)
