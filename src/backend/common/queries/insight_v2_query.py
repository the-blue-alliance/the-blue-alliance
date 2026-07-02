from typing import Any, Generator, List

from backend.common.models.insight_v2 import InsightV2
from backend.common.models.keys import DistrictAbbreviation, Year
from backend.common.queries.database_query import CachedDatabaseQuery
from backend.common.queries.dict_converters.insight_v2_converter import (
    InsightV2Converter,
    InsightV2Dict,
)
from backend.common.tasklets import typed_tasklet


class InsightV2YearQuery(CachedDatabaseQuery[List[InsightV2], List[InsightV2Dict]]):
    """All global (non-district) InsightV2 entities for a year, across all categories."""

    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = "insight_v2_{year}"
    DICT_CONVERTER = InsightV2Converter

    def __init__(self, year: Year) -> None:
        super().__init__(year=year)

    @typed_tasklet
    def _query_async(self, year: Year) -> Generator[Any, Any, List[InsightV2]]:
        insights = yield InsightV2.query(
            InsightV2.year == year,
            InsightV2.district_abbreviation == None,  # noqa: E711
        ).fetch_async()
        return insights


class InsightV2YearCategoryQuery(
    CachedDatabaseQuery[List[InsightV2], List[InsightV2Dict]]
):
    """All global (non-district) InsightV2 entities for a year filtered by category."""

    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = "insight_v2_{year}_{category}"
    DICT_CONVERTER = InsightV2Converter

    def __init__(self, year: Year, category: str) -> None:
        super().__init__(year=year, category=category)

    @typed_tasklet
    def _query_async(
        self, year: Year, category: str
    ) -> Generator[Any, Any, List[InsightV2]]:
        insights = yield InsightV2.query(
            InsightV2.year == year,
            InsightV2.category == category,
            InsightV2.district_abbreviation == None,  # noqa: E711
        ).fetch_async()
        return insights


class InsightV2YearDistrictQuery(
    CachedDatabaseQuery[List[InsightV2], List[InsightV2Dict]]
):
    """All InsightV2 entities for a year scoped to a specific district."""

    CACHE_VERSION = 0
    CACHE_KEY_FORMAT = "insight_v2_{year}_district_{district_abbreviation}"
    DICT_CONVERTER = InsightV2Converter

    def __init__(self, year: Year, district_abbreviation: DistrictAbbreviation) -> None:
        super().__init__(year=year, district_abbreviation=district_abbreviation)

    @typed_tasklet
    def _query_async(
        self, year: Year, district_abbreviation: DistrictAbbreviation
    ) -> Generator[Any, Any, List[InsightV2]]:
        insights = yield InsightV2.query(
            InsightV2.year == year,
            InsightV2.district_abbreviation == district_abbreviation,
        ).fetch_async()
        return insights


class InsightV2YearCategoryDistrictQuery(
    CachedDatabaseQuery[List[InsightV2], List[InsightV2Dict]]
):
    """All InsightV2 entities for a year, category, and district."""

    CACHE_VERSION = 0
    CACHE_KEY_FORMAT = "insight_v2_{year}_{category}_district_{district_abbreviation}"
    DICT_CONVERTER = InsightV2Converter

    def __init__(
        self,
        year: Year,
        category: str,
        district_abbreviation: DistrictAbbreviation,
    ) -> None:
        super().__init__(
            year=year, category=category, district_abbreviation=district_abbreviation
        )

    @typed_tasklet
    def _query_async(
        self,
        year: Year,
        category: str,
        district_abbreviation: DistrictAbbreviation,
    ) -> Generator[Any, Any, List[InsightV2]]:
        insights = yield InsightV2.query(
            InsightV2.year == year,
            InsightV2.category == category,
            InsightV2.district_abbreviation == district_abbreviation,
        ).fetch_async()
        return insights
