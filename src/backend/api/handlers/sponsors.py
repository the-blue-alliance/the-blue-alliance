from datetime import timedelta

from backend.api.handlers.decorators import api_authenticated
from backend.api.handlers.helpers.profiled_jsonify import (
    profiled_jsonify,
    TypedFlaskResponse,
)
from backend.api.handlers.helpers.track_call import track_call_after_response
from backend.common.decorators import cached_public
from backend.common.sitevars.platinum_sponsors import PlatinumSponsors


@api_authenticated
@cached_public(query_string=False, ttl=timedelta(hours=1))
def sponsors() -> TypedFlaskResponse[dict]:
    track_call_after_response("sponsors", "sponsors")
    return profiled_jsonify({"sponsors": PlatinumSponsors.sponsors()})
