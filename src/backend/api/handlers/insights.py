from flask import Response

from backend.api.handlers.decorators import api_authenticated
from backend.api.handlers.helpers.profiled_jsonify import profiled_jsonify
from backend.api.handlers.helpers.track_call import track_call_after_response
from backend.common.consts.api_version import ApiMajorVersion
from backend.common.decorators import cached_public
from backend.common.queries.insight_query import (
    InsightsLeaderboardsYearQuery,
    InsightsNotablesYearQuery,
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
