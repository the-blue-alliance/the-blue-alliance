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
from backend.common.models.keys import EventKey
from backend.common.queries.event_query import EventQuery


@validate_event_key
@api_authenticated
@cached_public
def event(event_key: EventKey, model_type: Optional[ModelType] = None) -> Response:
    track_call_after_response("event", event_key)

    event = EventQuery(event_key=event_key).fetch_dict(ApiMajorVersion.API_V3)
    if model_type is not None:
        event = filter_event_properties([event], model_type)[0]
    return jsonify(event)
