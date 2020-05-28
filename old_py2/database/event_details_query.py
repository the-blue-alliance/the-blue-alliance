from google.appengine.ext import ndb

from database.database_query import DatabaseQuery
from database.dict_converters.event_details_converter import EventDetailsConverter
from models.event_details import EventDetails


class EventDetailsQuery(DatabaseQuery):
    CACHE_VERSION = 0
    CACHE_KEY_FORMAT = 'event_details_{}'  # (event_key)
    DICT_CONVERTER = EventDetailsConverter

    @ndb.tasklet
    def _query_async(self):
        event_key = self._query_args[0]
        event_details = yield EventDetails.get_by_id_async(event_key)
        raise ndb.Return(event_details)
