from typing import Any, Generator, List

from backend.common.models.insight import Insight
from backend.common.models.keys import Year
from backend.common.queries.database_query import CachedDatabaseQuery
from backend.common.queries.dict_converters.insight_converter import (
    InsightConverter,
    InsightDict,
)
from backend.common.tasklets import typed_tasklet


class InsightsByNameQuery(CachedDatabaseQuery[List[Insight], List[InsightDict]]):
    CACHE_VERSION = 0
    CACHE_KEY_FORMAT = "insights_{insight_name}"
    DICT_CONVERTER = InsightConverter

    def __init__(self, insight_name: str) -> None:
        super().__init__(insight_name=insight_name)

    @typed_tasklet
    def _query_async(self, insight_name: str) -> Generator[Any, Any, List[InsightDict]]:
        insights = yield Insight.query(Insight.name == insight_name).fetch_async()
        return insights


class InsightsByNameAndYearQuery(CachedDatabaseQuery[List[Insight], List[InsightDict]]):
    CACHE_VERSION = 0
    CACHE_KEY_FORMAT = "insights_{insight_name}_{year}"
    DICT_CONVERTER = InsightConverter

    def __init__(self, insight_name: str, year: Year) -> None:
        super().__init__(insight_name=insight_name, year=year)

    @typed_tasklet
    def _query_async(
        self, insight_name: str, year: Year
    ) -> Generator[Any, Any, List[InsightDict]]:
        insights = yield Insight.query(
            Insight.name == insight_name, Insight.year == year
        ).fetch_async()
        return insights
