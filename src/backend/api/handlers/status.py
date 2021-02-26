from flask import jsonify, Response

from backend.api.handlers.decorators import api_authenticated
from backend.api.handlers.helpers.make_error_response import make_error_response
from backend.api.handlers.helpers.track_call import track_call_after_response
from backend.common.decorators import cached_public
from backend.common.models.sitevar import Sitevar


@api_authenticated
@cached_public
def status() -> Response:
    track_call_after_response("status", "status")

    status_sitevar_future = Sitevar.get_by_id_async("apistatus")
    fmsapi_sitevar_future = Sitevar.get_by_id_async("apistatus.fmsapi_down")
    down_events_sitevar_future = Sitevar.get_by_id_async("apistatus.down_events")

    # Error out if no sitevar found
    status_sitevar = status_sitevar_future.get_result()
    if not status_sitevar:
        return make_error_response(404, {"404": "API Status Not Found"})

    status_dict = status_sitevar.contents
    down_events_sitevar = down_events_sitevar_future.get_result()
    down_events_list = down_events_sitevar.contents if down_events_sitevar else None

    fmsapi_sitevar = fmsapi_sitevar_future.get_result()
    status_dict["is_datafeed_down"] = (
        True if fmsapi_sitevar and fmsapi_sitevar.contents is True else False
    )
    status_dict["down_events"] = (
        down_events_list if down_events_list is not None else []
    )

    return jsonify(status_dict)
