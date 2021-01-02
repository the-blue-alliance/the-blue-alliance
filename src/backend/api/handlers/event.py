from typing import Optional

from flask import jsonify, Response

from backend.api.handlers.decorators import api_authenticated, validate_event_key
from backend.api.handlers.helpers.model_properties import (
    filter_event_properties,
    ModelType,
)
from backend.api.handlers.helpers.track_call import track_call_after_response
from backend.common.consts.api_version import ApiMajorVersion
from backend.common.decorators import cached_public
from backend.common.helpers.season_helper import SeasonHelper
from backend.common.models.keys import EventKey
from backend.common.queries.event_query import EventListQuery, EventQuery


@api_authenticated
@validate_event_key
@cached_public
def event(event_key: EventKey, model_type: Optional[ModelType] = None) -> Response:
    """
    Returns details about one event, specified by |event_key|.
    """
    track_call_after_response("event", event_key, model_type)

    event = EventQuery(event_key=event_key).fetch_dict(ApiMajorVersion.API_V3)
    if model_type is not None:
        event = filter_event_properties([event], model_type)[0]
    return jsonify(event)


@api_authenticated
@cached_public
def event_list_all(model_type: Optional[ModelType] = None) -> Response:
    """
    Returns a list of all events.
    """
    track_call_after_response("event/list", "all", model_type)

    futures = []
    for year in SeasonHelper.get_valid_years():
        futures.append(
            EventListQuery(year=year).fetch_dict_async(ApiMajorVersion.API_V3)
        )

    events = []
    for future in futures:
        partial_event_list = future.get_result()
        events += partial_event_list

    if model_type is not None:
        events = filter_event_properties(events, model_type)
    return jsonify(events)


@api_authenticated
@cached_public
def event_list_year(year: int, model_type: Optional[ModelType] = None) -> Response:
    """
    Returns a list of all events for a given year.
    """
    track_call_after_response("event/list", str(year), model_type)

    events = EventListQuery(year=year).fetch_dict(ApiMajorVersion.API_V3)

    if model_type is not None:
        events = filter_event_properties(events, model_type)
    return jsonify(events)
