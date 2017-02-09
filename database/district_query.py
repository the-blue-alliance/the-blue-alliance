from google.appengine.ext import ndb

from consts.event_type import EventType
from database.database_query import DatabaseQuery
from database.dict_converters.district_converter import DistrictConverter
from models.district import District
from models.event import Event


class DistrictQuery(DatabaseQuery):
    CACHE_VERSION = 0
    CACHE_KEY_FORMAT = 'district_{}'  # (district_key)
    DICT_CONVERTER = None

    @ndb.tasklet
    def _query_async(self):
        district_key = self._query_args[0]
        district = yield District.get_by_id_async(district_key)
        raise ndb.Return(district)


class DistrictChampsInYearQuery(DatabaseQuery):
    CACHE_VERSION = 0
    CACHE_KEY_FORMAT = 'district_list_{}'  # (year)
    DICT_CONVERTER = None  # Not exposed in API, not needed

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
    DICT_CONVERTER = DistrictConverter

    @ndb.tasklet
    def _query_async(self):
        year = self._query_args[0]
        district_keys = yield District.query(District.year == year).fetch_async(keys_only=True)
        districts = yield ndb.get_multi_async(district_keys)
        raise ndb.Return(districts)


class DistrictHistoryQuery(DatabaseQuery):
    CACHE_VERSION = 0
    CACHE_KEY_FORMAT = "district_history_{}"  # (abbreviation)
    DICT_CONVERTER = DistrictConverter

    @ndb.tasklet
    def _query_async(self):
        abbreviation = self._query_args[0]
        district_keys = yield District.query(District.abbreviation == abbreviation).fetch_async(keys_only=True)
        districts = yield ndb.get_multi_async(district_keys)
        raise ndb.Return(districts)

