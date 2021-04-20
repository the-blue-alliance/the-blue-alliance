from flask import jsonify, Response

from backend.api.handlers.decorators import api_authenticated
from backend.api.handlers.helpers.track_call import track_call_after_response
from backend.common.decorators import cached_public
from backend.common.models.sitevar import Sitevar
from backend.common.sitevars.apistatus import ApiStatus


@api_authenticated
@cached_public
def status() -> Response:
    track_call_after_response("status", "status")

    # TODO: Remove Sitevar usage for Sitevar classes
    fmsapi_sitevar_future = Sitevar.get_by_id_async("apistatus.fmsapi_down")
    down_events_sitevar_future = Sitevar.get_by_id_async("apistatus.down_events")

    status = dict()
    status.update(ApiStatus.status())

    down_events_sitevar = down_events_sitevar_future.get_result()
    down_events_list = down_events_sitevar.contents if down_events_sitevar else None

    fmsapi_sitevar = fmsapi_sitevar_future.get_result()
    status["is_datafeed_down"] = (
        True if fmsapi_sitevar and fmsapi_sitevar.contents is True else False
    )
    status["down_events"] = down_events_list if down_events_list is not None else []

    return jsonify(status)
