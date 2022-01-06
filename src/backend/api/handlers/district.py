from typing import Optional

from flask import jsonify, Response

from backend.api.handlers.decorators import api_authenticated, validate_district_key
from backend.api.handlers.helpers.model_properties import (
    filter_event_properties,
    filter_team_properties,
    ModelType,
)
from backend.api.handlers.helpers.track_call import track_call_after_response
from backend.common.consts.api_version import ApiMajorVersion
from backend.common.decorators import cached_public
from backend.common.models.keys import DistrictKey
from backend.common.queries.district_query import DistrictsInYearQuery
from backend.common.queries.event_query import DistrictEventsQuery
from backend.common.queries.team_query import DistrictTeamsQuery


@api_authenticated
@validate_district_key
@cached_public
def district_events(
    district_key: DistrictKey, model_type: Optional[ModelType] = None
) -> Response:
    """
    Returns a list of events for a given DistrictKey.
    """
    track_call_after_response("district/events", district_key, model_type)

    events = DistrictEventsQuery(district_key=district_key).fetch_dict(
        ApiMajorVersion.API_V3
    )
    if model_type is not None:
        events = filter_event_properties(events, model_type)
    return jsonify(events)


@api_authenticated
@validate_district_key
@cached_public
def district_teams(
    district_key: DistrictKey, model_type: Optional[ModelType] = None
) -> Response:
    """
    Returns a list of teams for a given DistrictKey.
    """
    track_call_after_response("district/teams", district_key, model_type)

    teams = DistrictTeamsQuery(district_key=district_key).fetch_dict(
        ApiMajorVersion.API_V3
    )
    if model_type is not None:
        teams = filter_team_properties(teams, model_type)
    return jsonify(teams)


@api_authenticated
@cached_public
def district_list_year(year: int) -> Response:
    """
    Returns a list of all districts for a given year.
    """
    track_call_after_response("district/list", str(year))

    district = DistrictsInYearQuery(year=year).fetch_dict(ApiMajorVersion.API_V3)
    return jsonify(district)
