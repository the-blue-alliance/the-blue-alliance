from flask import jsonify, Response

from backend.api.handlers.decorators import api_authenticated, validate_event_key
from backend.common.consts.api_version import ApiMajorVersion
from backend.common.decorators import cached_public
from backend.common.models.keys import EventKey
from backend.common.queries.event_query import EventQuery


@validate_event_key
@api_authenticated
@cached_public
def event(event_key: EventKey) -> Response:
    return jsonify(EventQuery(event_key=event_key).fetch_dict(ApiMajorVersion.API_V3))
