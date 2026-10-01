from flask import abort, Response

from backend.api.handlers.decorators import api_authenticated, validate_etag
from backend.api.handlers.helpers.model_query_response import models_query_response
from backend.api.handlers.helpers.track_call import track_call_after_response
from backend.common.decorators import cached_public
from backend.common.models.insight_v2 import InsightCategory
from backend.common.models.keys import DistrictAbbreviation
from backend.common.queries.insight_query import (
    InsightsLeaderboardsYearQuery,
    InsightsNotablesYearQuery,
)
from backend.common.queries.insight_v2_query import (
    InsightV2YearCategoryDistrictQuery,
    InsightV2YearCategoryQuery,
    InsightV2YearDistrictQuery,
    InsightV2YearQuery,
)

_VALID_INSIGHT_V2_CATEGORIES = frozenset(
    {
        InsightCategory.LEADERBOARD,
        InsightCategory.STREAK,
        InsightCategory.TIMESERIES,
        InsightCategory.GAME_STATS,
        InsightCategory.CLUBS,
    }
)


@api_authenticated
@cached_public(query_string=False)
@validate_etag
def insights_leaderboards_year(year: int) -> Response:
    track_call_after_response("insights/leaderboards", str(year))
    return models_query_response(InsightsLeaderboardsYearQuery(year=year))


@api_authenticated
@cached_public(query_string=False)
@validate_etag
def insights_notables_year(year: int) -> Response:
    track_call_after_response("insights/notables", str(year))
    return models_query_response(InsightsNotablesYearQuery(year=year))


@api_authenticated
@cached_public(query_string=False)
@validate_etag
def insights_v2_year(year: int) -> Response:
    track_call_after_response("insights/v2", str(year))
    return models_query_response(InsightV2YearQuery(year=year))


@api_authenticated
@cached_public(query_string=False)
@validate_etag
def insights_v2_year_category(year: int, category: str) -> Response:
    if category not in _VALID_INSIGHT_V2_CATEGORIES:
        abort(404)

    track_call_after_response("insights/v2/category", f"{year}/{category}")
    return models_query_response(
        InsightV2YearCategoryQuery(year=year, category=category)
    )


@api_authenticated
@cached_public(query_string=False)
@validate_etag
def insights_v2_year_district(
    year: int, district_abbreviation: DistrictAbbreviation
) -> Response:
    track_call_after_response("insights/v2/district", f"{year}/{district_abbreviation}")
    return models_query_response(
        InsightV2YearDistrictQuery(
            year=year, district_abbreviation=district_abbreviation
        )
    )


@api_authenticated
@cached_public(query_string=False)
@validate_etag
def insights_v2_year_category_district(
    year: int, category: str, district_abbreviation: DistrictAbbreviation
) -> Response:
    if category not in _VALID_INSIGHT_V2_CATEGORIES:
        abort(404)

    track_call_after_response(
        "insights/v2/category/district", f"{year}/{category}/{district_abbreviation}"
    )
    return models_query_response(
        InsightV2YearCategoryDistrictQuery(
            year=year, category=category, district_abbreviation=district_abbreviation
        )
    )
