from flask import make_response, Response

from backend.api.handlers.decorators import api_authenticated
from backend.api.handlers.helpers.profiled_jsonify import profiled_jsonify
from backend.api.handlers.helpers.track_call import track_call_after_response
from backend.common.decorators import cached_public
from backend.common.helpers.season_helper import SeasonHelper
from backend.common.models.keys import Year
from backend.common.models.regional_champs_pool import RegionalChampsPool


@api_authenticated
@cached_public
def regional_rankings(year: Year) -> Response:
    """
    Returns the regional advancement rankings
    """
    if not SeasonHelper.is_valid_regional_pool_year(year):
        return make_response(
            {"Error": f"{year} is not a valid year for regional rankings"}, 404
        )

    track_call_after_response("regional_rankings", f"{year}")
    pool = RegionalChampsPool.get_by_id(RegionalChampsPool.render_key_name(year))
    if not pool:
        return make_response({"Error": f"No regional rankings found for {year}"}, 404)

    return profiled_jsonify(pool.rankings)


@api_authenticated
@cached_public
def regional_advancement(year: Year) -> Response:
    """
    Returns the regional advancement qualification info
    """
    if not SeasonHelper.is_valid_regional_pool_year(year):
        return make_response(
            {"Error": f"{year} is not a valid year for regional advancement"}, 404
        )

    track_call_after_response("regional_rankings", f"{year}")
    pool = RegionalChampsPool.get_by_id(RegionalChampsPool.render_key_name(year))
    if not pool:
        return make_response(
            {"Error": f"No regional advancement found for {year}"}, 404
        )

    return profiled_jsonify(pool.advancement)
