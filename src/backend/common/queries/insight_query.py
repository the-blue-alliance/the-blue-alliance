from typing import Any, Generator, List

from backend.common.models.insight import Insight
from backend.common.models.keys import Year
from backend.common.queries.database_query import CachedDatabaseQuery
from backend.common.queries.dict_converters.insight_converter import (
    InsightConverter,
    InsightDict,
)
from backend.common.tasklets import typed_tasklet


class InsightsLeaderboardsYearQuery(
    CachedDatabaseQuery[List[Insight], List[InsightDict]]
):
    CACHE_VERSION = 0
    CACHE_KEY_FORMAT = "insights_leaderboards_{year}"
    DICT_CONVERTER = InsightConverter

    def __init__(self, year: Year) -> None:
        super().__init__(year=year)

    @typed_tasklet
    def _query_async(self, year: Year) -> Generator[Any, Any, List[Insight]]:
        insight_names = []
        for insight_type in Insight.TYPED_LEADERBOARD_MATCH_INSIGHTS.union(
            Insight.TYPED_LEADERBOARD_AWARD_INSIGHTS
        ):
            insight_names.append(Insight.INSIGHT_NAMES[insight_type])

        insights = yield Insight.query(
            Insight.name.IN(insight_names),
            Insight.year == year,
        ).fetch_async()
        return insights


class InsightsNotablesYearQuery(CachedDatabaseQuery[List[Insight], List[InsightDict]]):
    CACHE_VERSION = 0
    CACHE_KEY_FORMAT = "insights_notables_{year}"
    DICT_CONVERTER = InsightConverter

    def __init__(self, year: Year) -> None:
        super().__init__(year=year)

    @typed_tasklet
    def _query_async(self, year: Year) -> Generator[Any, Any, List[Insight]]:
        insight_names = []
        for insight_type in Insight.NOTABLE_INSIGHTS:
            insight_names.append(Insight.INSIGHT_NAMES[insight_type])

        insights = yield Insight.query(
            Insight.name.IN(insight_names),
            Insight.year == year,
        ).fetch_async()
        return insights
