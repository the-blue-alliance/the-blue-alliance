from google.appengine.ext import ndb

from consts.event_type import EventType
from database.database_query import DatabaseQuery
from database.dict_converters.district_converter import DistrictListConverter
from models.district import District
from models.event import Event


class DistrictListQuery(DatabaseQuery):
    CACHE_VERSION = 0
    CACHE_KEY_FORMAT = 'district_list_{}'  # (year)
    DICT_CONVERTER = DistrictListConverter

    @ndb.tasklet
    def _query_async(self):
        year = self._query_args[0]
        all_cmp_event_keys = yield Event.query(
            Event.year == int(year),
            Event.event_type_enum == EventType.DISTRICT_CMP).fetch_async(keys_only=True)
        events = yield ndb.get_multi_async(all_cmp_event_keys)
        raise ndb.Return(events)


class DistrictsInYearQuery(DatabaseQuery):
    CACHE_VERSION = 0
    CACHE_KEY_FORMAT = "districts_in_year_{}"  # (year)
    DICT_CONVERTER = None  # For now (TODO)

    @ndb.tasklet
    def _query_async(self):
        year = self._query_args[0]
        keys_future = yield District.query(District.year == year).fetch_async(keys_only=True)
        districts = yield ndb.get_multi_async(keys_future)
        raise ndb.Return(districts)
