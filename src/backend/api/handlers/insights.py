from flask import abort, Response

from backend.api.handlers.decorators import api_authenticated
from backend.api.handlers.helpers.profiled_jsonify import profiled_jsonify
from backend.api.handlers.helpers.track_call import track_call_after_response
from backend.common.consts.api_version import ApiMajorVersion
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
    }
)


@api_authenticated
@cached_public
def insights_leaderboards_year(year: int) -> Response:
    track_call_after_response("insights/leaderboards", str(year))

    insights = InsightsLeaderboardsYearQuery(year=year).fetch_dict(
        ApiMajorVersion.API_V3
    )

    return profiled_jsonify(insights)


@api_authenticated
@cached_public
def insights_notables_year(year: int) -> Response:
    track_call_after_response("insights/notables", str(year))

    insights = InsightsNotablesYearQuery(year=year).fetch_dict(ApiMajorVersion.API_V3)
    return profiled_jsonify(insights)


@api_authenticated
@cached_public
def insights_v2_year(year: int) -> Response:
    track_call_after_response("insights/v2", str(year))

    insights = InsightV2YearQuery(year=year).fetch_dict(ApiMajorVersion.API_V3)
    return profiled_jsonify(insights)


@api_authenticated
@cached_public
def insights_v2_year_category(year: int, category: str) -> Response:
    if category not in _VALID_INSIGHT_V2_CATEGORIES:
        abort(404)

    track_call_after_response("insights/v2/category", f"{year}/{category}")

    insights = InsightV2YearCategoryQuery(year=year, category=category).fetch_dict(
        ApiMajorVersion.API_V3
    )
    return profiled_jsonify(insights)


@api_authenticated
@cached_public
def insights_v2_year_district(
    year: int, district_abbreviation: DistrictAbbreviation
) -> Response:
    track_call_after_response("insights/v2/district", f"{year}/{district_abbreviation}")

    insights = InsightV2YearDistrictQuery(
        year=year, district_abbreviation=district_abbreviation
    ).fetch_dict(ApiMajorVersion.API_V3)
    return profiled_jsonify(insights)


@api_authenticated
@cached_public
def insights_v2_year_category_district(
    year: int, category: str, district_abbreviation: DistrictAbbreviation
) -> Response:
    if category not in _VALID_INSIGHT_V2_CATEGORIES:
        abort(404)

    track_call_after_response(
        "insights/v2/category/district", f"{year}/{category}/{district_abbreviation}"
    )

    insights = InsightV2YearCategoryDistrictQuery(
        year=year, category=category, district_abbreviation=district_abbreviation
    ).fetch_dict(ApiMajorVersion.API_V3)
    return profiled_jsonify(insights)
