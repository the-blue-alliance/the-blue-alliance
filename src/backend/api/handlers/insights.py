from flask import Response

from backend.api.handlers.decorators import api_authenticated
from backend.api.handlers.helpers.profiled_jsonify import profiled_jsonify
from backend.api.handlers.helpers.track_call import track_call_after_response
from backend.common.consts.api_version import ApiMajorVersion
from backend.common.decorators import cached_public
from backend.common.models.insight import Insight
from backend.common.queries.insight_query import InsightsByNameAndYearQuery


@api_authenticated
@cached_public
def insights_leaderboards_year(year: int) -> Response:
    track_call_after_response("insights/leaderboards", str(year))
    futures = []
    for insight_type in Insight.TYPED_LEADERBOARD_MATCH_INSIGHTS.union(
        Insight.TYPED_LEADERBOARD_AWARD_INSIGHTS
    ):
        futures.append(
            InsightsByNameAndYearQuery(
                insight_name=Insight.INSIGHT_NAMES[insight_type], year=year
            ).fetch_dict_async(ApiMajorVersion.API_V3)
        )

    insights = []
    for future in futures:
        insights.extend(future.get_result())

    return profiled_jsonify(insights)
