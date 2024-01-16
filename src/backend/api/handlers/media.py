from datetime import timedelta

from flask import Response

from backend.api.handlers.decorators import api_authenticated
from backend.api.handlers.helpers.profiled_jsonify import profiled_jsonify
from backend.api.handlers.helpers.track_call import track_call_after_response
from backend.common.consts.media_tag import TAG_NAMES, TAG_URL_NAMES
from backend.common.decorators import cached_public


@api_authenticated
@cached_public(ttl=timedelta(days=1))
def media_tags() -> Response:
    """
    Returns a list of media tag names and codes.
    """
    track_call_after_response("media/tags")

    media_tags = []
    for index in TAG_NAMES:
        media_tags.append({"name": TAG_NAMES[index], "code": TAG_URL_NAMES[index]})
    return profiled_jsonify(media_tags)
