from datetime import datetime, timedelta
from typing import Optional

from flask import Response

from backend.api.handlers.decorators import api_authenticated, validate_keys
from backend.api.handlers.helpers.model_properties import (
    filter_match_properties,
    ModelType,
)
from backend.api.handlers.helpers.profiled_jsonify import profiled_jsonify
from backend.api.handlers.helpers.track_call import track_call_after_response
from backend.common.consts.api_version import ApiMajorVersion
from backend.common.decorators import cached_public
from backend.common.flask_cache import make_cached_response
from backend.common.models.keys import MatchKey
from backend.common.models.zebra_motionworks import ZebraMotionWorks
from backend.common.queries.match_query import MatchQuery


@api_authenticated
@validate_keys
@cached_public
def match(match_key: MatchKey, model_type: Optional[ModelType] = None) -> Response:
    """
    Returns details about one match, specified by |match_key|.
    """
    track_call_after_response("match", match_key, model_type)

    year = int(match_key[:4])
    match = MatchQuery(match_key=match_key).fetch_dict(ApiMajorVersion.API_V3)
    if model_type is not None:
        match = filter_match_properties([match], model_type)[0]
    return make_cached_response(
        profiled_jsonify(match),
        ttl=timedelta(seconds=61) if year == datetime.now().year else timedelta(days=1),
    )


@api_authenticated
@validate_keys
@cached_public
def zebra_motionworks(match_key: MatchKey) -> Response:
    """
    Returns Zebra Motionworks data for a given match.
    """
    track_call_after_response("zebra_motionworks_match", match_key)

    zebra_data = ZebraMotionWorks.get_by_id(match_key)
    data = zebra_data.data if zebra_data is not None else None
    return profiled_jsonify(data)
