from typing import Any, Optional

from backend.api.handlers.decorators import (
    api_authenticated,
    validate_etag,
    validate_keys,
)
from backend.api.handlers.helpers.model_properties import (
    filter_match_properties,
    ModelType,
)
from backend.api.handlers.helpers.model_query_response import model_query_response
from backend.api.handlers.helpers.profiled_jsonify import (
    profiled_jsonify,
    TypedFlaskResponse,
)
from backend.api.handlers.helpers.track_call import track_call_after_response
from backend.common.decorators import cached_public
from backend.common.models.keys import MatchKey
from backend.common.models.zebra_motionworks import ZebraMotionWorks
from backend.common.queries.dict_converters.match_converter import MatchDict
from backend.common.queries.match_query import MatchQuery


@api_authenticated
@cached_public
@validate_etag
@validate_keys
def match(
    match_key: MatchKey, model_type: Optional[ModelType] = None
) -> TypedFlaskResponse[MatchDict]:
    """
    Returns details about one match, specified by |match_key|.
    """
    track_call_after_response("match", match_key, model_type)
    return model_query_response(
        MatchQuery(match_key=match_key),
        model_type=model_type,
        filter_func=filter_match_properties,
    )


@api_authenticated
@cached_public
@validate_etag
@validate_keys
def zebra_motionworks(match_key: MatchKey) -> TypedFlaskResponse[Any]:
    """
    Returns Zebra Motionworks data for a given match.
    """
    track_call_after_response("zebra_motionworks_match", match_key)

    zebra_data = ZebraMotionWorks.get_by_id(match_key)
    data = zebra_data.data if zebra_data is not None else None
    return profiled_jsonify(data)
