from typing import Optional

from flask import jsonify, Response

from backend.api.handlers.decorators import api_authenticated, validate_keys
from backend.api.handlers.helpers.model_properties import (
    filter_match_properties,
    ModelType,
)
from backend.api.handlers.helpers.track_call import track_call_after_response
from backend.common.consts.api_version import ApiMajorVersion
from backend.common.decorators import cached_public
from backend.common.models.keys import MatchKey
from backend.common.queries.match_query import MatchQuery


@api_authenticated
@validate_keys
@cached_public
def match(match_key: MatchKey, model_type: Optional[ModelType] = None) -> Response:
    """
    Returns details about one match, specified by |match_key|.
    """
    track_call_after_response("match", match_key, model_type)

    match = MatchQuery(match_key=match_key).fetch_dict(ApiMajorVersion.API_V3)
    if model_type is not None:
        match = filter_match_properties([match], model_type)[0]
    return jsonify(match)
