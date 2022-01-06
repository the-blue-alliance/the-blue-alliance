from flask import jsonify, Response

from backend.api.handlers.decorators import api_authenticated
from backend.api.handlers.helpers.track_call import track_call_after_response
from backend.common.consts.api_version import ApiMajorVersion
from backend.common.decorators import cached_public
from backend.common.queries.district_query import DistrictsInYearQuery


@api_authenticated
@cached_public
def district_list_year(year: int) -> Response:
    """
    Returns a list of all districts for a given year.
    """
    track_call_after_response("district/list", str(year))

    district = DistrictsInYearQuery(year=year).fetch_dict(ApiMajorVersion.API_V3)
    return jsonify(district)
