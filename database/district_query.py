from google.appengine.ext import ndb

from consts.event_type import EventType
from database.database_query import DatabaseQuery
from database.dict_converters.district_converter import DistrictConverter
from models.district import District
from models.event import Event

# These district codes are equiavlent due to FIRST renaming districts
CODE_MAP = {
    # Old to new
    'mar': 'fma',
    'nc': 'fnc',
    # New to old
    'fma': 'mar',
    'fnc': 'nc',
}


def get_equivalent_codes(code):
    # Returns a list of equivalent district codes
    codes = [code]
    if code in CODE_MAP:
        codes.append(CODE_MAP[code])
    return codes


def get_equivalent_keys(district_key):
    # Returns a list of equivalent district keys
    year = district_key[:4]
    code = district_key[4:]
    return ['{}{}'.format(year, equiv_code) for equiv_code in get_equivalent_codes(code)]


class DistrictQuery(DatabaseQuery):
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = 'district_{}'  # (district_key)
    DICT_CONVERTER = None

    @ndb.tasklet
    def _query_async(self):
        district_key = self._query_args[0]
        # Fetch all equivalent keys
        keys = get_equivalent_keys(district_key)
        districts = yield ndb.get_multi_async([ndb.Key(District, key) for key in keys])
        for district in districts:
            if district:
                # Return first key that exists
                raise ndb.Return(district)
        raise ndb.Return(None)


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
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = "district_history_{}"  # (abbreviation)
    DICT_CONVERTER = DistrictConverter

    @ndb.tasklet
    def _query_async(self):
        abbreviation = self._query_args[0]
        district_keys = yield District.query(District.abbreviation.IN(get_equivalent_codes(abbreviation))).fetch_async(keys_only=True)
        districts = yield ndb.get_multi_async(district_keys)
        raise ndb.Return(districts)
