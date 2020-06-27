from typing import List, Optional

from google.cloud import ndb

from backend.common.consts.event_type import EventType
from backend.common.consts.renamed_districts import RenamedDistricts
from backend.common.models.district import District
from backend.common.models.event import Event
from backend.common.models.keys import DistrictAbbreviation, DistrictKey
from backend.common.queries.database_query import DatabaseQuery
from backend.common.queries.dict_converters.district_converter import DistrictConverter


class DistrictQuery(DatabaseQuery[Optional[District]]):
    DICT_CONVERTER = DistrictConverter

    @ndb.tasklet
    def _query_async(self, district_key: DistrictKey) -> Optional[District]:
        # Fetch all equivalent keys
        keys = RenamedDistricts.get_equivalent_keys(district_key)
        districts = yield ndb.get_multi_async([ndb.Key(District, key) for key in keys])
        for district in districts:
            if district:
                # Return first key that exists
                return district
        return None


class DistrictChampsInYearQuery(DatabaseQuery[List[District]]):
    DICT_CONVERTER = DistrictConverter

    @ndb.tasklet
    def _query_async(self, year: int) -> List[District]:
        all_cmp_event_keys = yield Event.query(
            Event.year == year, Event.event_type_enum == EventType.DISTRICT_CMP
        ).fetch_async(keys_only=True)
        events = yield ndb.get_multi_async(all_cmp_event_keys)
        return list(events)


class DistrictsInYearQuery(DatabaseQuery[List[District]]):
    DICT_CONVERTER = DistrictConverter

    @ndb.tasklet
    def _query_async(self, year: int) -> List[District]:
        district_keys = yield District.query(District.year == year).fetch_async(
            keys_only=True
        )
        districts = yield ndb.get_multi_async(district_keys)
        return list(districts)


class DistrictHistoryQuery(DatabaseQuery[List[District]]):
    DICT_CONVERTER = DistrictConverter

    @ndb.tasklet
    def _query_async(self, abbreviation: DistrictAbbreviation) -> List[District]:
        district_keys = yield District.query(
            District.abbreviation.IN(
                RenamedDistricts.get_equivalent_codes(abbreviation)
            )
        ).fetch_async(keys_only=True)
        districts = yield ndb.get_multi_async(district_keys)
        return list(districts)
