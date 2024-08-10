from flask import Response

from backend.api.handlers.decorators import api_authenticated
from backend.api.handlers.helpers.profiled_jsonify import profiled_jsonify
from backend.api.handlers.helpers.track_call import track_call_after_response
from backend.common.consts.api_version import ApiMajorVersion
from backend.common.consts.insight_type import LEADERBOARD_INSIGHTS, NOTABLES_INSIGHTS
from backend.common.decorators import cached_public
from backend.common.models.insight import Insight
from backend.common.queries.insight_query import (
    InsightsByNameAndYearQuery,
    InsightsByNameQuery,
)


@cached_public
def insights_leaderboards_all() -> Response:
    track_call_after_response("insights/leaderboards/all")
    futures = []
    for insight_type in LEADERBOARD_INSIGHTS:
        futures.append(
            InsightsByNameQuery(
                insight_name=Insight.INSIGHT_NAMES[insight_type]
            ).fetch_dict_async(ApiMajorVersion.API_V3)
        )

    insights = []
    for future in futures:
        insights.extend(future.get_result())

    return profiled_jsonify(insights)


@cached_public
def insights_leaderboards_year(year: int) -> Response:
    track_call_after_response("insights/leaderboards", year)
    futures = []
    for insight_type in LEADERBOARD_INSIGHTS:
        futures.append(
            InsightsByNameAndYearQuery(
                insight_name=Insight.INSIGHT_NAMES[insight_type], year=year
            ).fetch_dict_async(ApiMajorVersion.API_V3)
        )

    insights = []
    for future in futures:
        insights.extend(future.get_result())

    return profiled_jsonify(insights)


@cached_public
def insights_notables_all() -> Response:
    track_call_after_response("insights/notables/all")
    futures = []
    for notable_type in NOTABLES_INSIGHTS:
        futures.append(
            InsightsByNameQuery(
                insight_name=Insight.INSIGHT_NAMES[notable_type]
            ).fetch_dict_async(ApiMajorVersion.API_V3)
        )

    insights = []
    for future in futures:
        insights.extend(future.get_result())

    return profiled_jsonify(insights)


@cached_public
def insights_notables_year(year: int) -> Response:
    track_call_after_response("insights/notables", year)
    futures = []
    for notable_type in NOTABLES_INSIGHTS:
        futures.append(
            InsightsByNameAndYearQuery(
                insight_name=Insight.INSIGHT_NAMES[notable_type], year=year
            ).fetch_dict_async(ApiMajorVersion.API_V3)
        )

    insights = []
    for future in futures:
        insights.extend(future.get_result())

    return profiled_jsonify(insights)
