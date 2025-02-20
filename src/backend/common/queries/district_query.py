from typing import Any, Generator, List, Optional

from google.appengine.ext import ndb

from backend.common.consts.renamed_districts import RenamedDistricts
from backend.common.models.district import District
from backend.common.models.district_team import DistrictTeam
from backend.common.models.keys import DistrictAbbreviation, DistrictKey, TeamKey, Year
from backend.common.models.team import Team
from backend.common.queries.database_query import CachedDatabaseQuery
from backend.common.queries.dict_converters.district_converter import (
    DistrictConverter,
    DistrictDict,
)
from backend.common.tasklets import typed_tasklet


class DistrictQuery(CachedDatabaseQuery[Optional[District], Optional[DistrictDict]]):
    CACHE_VERSION = 2
    CACHE_KEY_FORMAT = "district_{district_key}"
    DICT_CONVERTER = DistrictConverter

    def __init__(self, district_key: DistrictKey) -> None:
        super().__init__(district_key=district_key)

    @typed_tasklet
    def _query_async(
        self, district_key: DistrictKey
    ) -> Generator[Any, Any, Optional[District]]:
        # Fetch all equivalent keys
        keys = RenamedDistricts.get_equivalent_keys(district_key)
        districts = yield ndb.get_multi_async([ndb.Key(District, key) for key in keys])
        for district in districts:
            if district:
                # Return first key that exists
                return district
        return None


class DistrictsInYearQuery(CachedDatabaseQuery[List[District], List[DistrictDict]]):
    CACHE_VERSION = 0
    CACHE_KEY_FORMAT = "districts_in_year_{year}"
    DICT_CONVERTER = DistrictConverter

    def __init__(self, year: Year) -> None:
        super().__init__(year=year)

    @typed_tasklet
    def _query_async(self, year: Year) -> Generator[Any, Any, List[District]]:
        district_keys = yield District.query(District.year == year).fetch_async(
            keys_only=True
        )
        districts = yield ndb.get_multi_async(district_keys)
        return list(districts)


class DistrictHistoryQuery(CachedDatabaseQuery[List[District], List[DistrictDict]]):
    CACHE_VERSION = 2
    CACHE_KEY_FORMAT = "district_history_{abbreviation}"
    DICT_CONVERTER = DistrictConverter

    def __init__(self, abbreviation: DistrictAbbreviation) -> None:
        super().__init__(abbreviation=abbreviation)

    @typed_tasklet
    def _query_async(
        self, abbreviation: DistrictAbbreviation
    ) -> Generator[Any, Any, List[District]]:
        district_keys = yield District.query(
            District.abbreviation.IN(
                RenamedDistricts.get_equivalent_codes(abbreviation)
            )
        ).fetch_async(keys_only=True)
        districts = yield ndb.get_multi_async(district_keys)
        return list(districts)


class TeamDistrictsQuery(CachedDatabaseQuery[List[District], List[DistrictDict]]):
    CACHE_VERSION = 2
    CACHE_KEY_FORMAT = "team_districts_{team_key}"
    DICT_CONVERTER = DistrictConverter

    def __init__(self, team_key: TeamKey) -> None:
        super().__init__(team_key=team_key)

    @typed_tasklet
    def _query_async(self, team_key: TeamKey) -> Generator[Any, Any, List[District]]:
        district_team_keys = yield DistrictTeam.query(
            DistrictTeam.team == ndb.Key(Team, team_key)
        ).fetch_async(keys_only=True)
        districts = yield ndb.get_multi_async(
            [ndb.Key(District, dtk.id().split("_")[0]) for dtk in district_team_keys]
        )
        return list(filter(lambda x: x is not None, districts))


class DistrictAbbreviationQuery(
    CachedDatabaseQuery[List[District], List[DistrictDict]]
):
    CACHE_VERSION = 2
    CACHE_KEY_FORMAT = "district_abbreviation_{abbreviation}"
    DICT_CONVERTER = DistrictConverter

    def __init__(self, abbreviation: DistrictAbbreviation) -> None:
        super().__init__(abbreviation=abbreviation)

    @typed_tasklet
    def _query_async(
        self, abbreviation: DistrictAbbreviation
    ) -> Generator[Any, Any, List[District]]:
        all_abbreviations = RenamedDistricts.get_equivalent_codes(abbreviation)

        district_keys = yield District.query(
            District.abbreviation.IN(all_abbreviations)
        ).fetch_async(keys_only=True)
        districts = yield ndb.get_multi_async(district_keys)

        return list(sorted(districts, key=lambda x: x.year))
