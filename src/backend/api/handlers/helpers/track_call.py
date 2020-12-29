from flask import request

from backend.common.google_analytics import GoogleAnalytics
from backend.common.models.api_auth_access import ApiAuthAccess
from backend.common.run_after_response import run_after_response


def track_call_after_response(api_action: str, api_label: str) -> None:
    auth_key = request.headers.get("X-TBA-Auth-Key", request.args.get("X-TBA-Auth-Key"))
    auth_owner_id = ApiAuthAccess.get_by_id(auth_key).owner.id()

    @run_after_response
    def track_call():
        GoogleAnalytics.track_event(
            auth_owner_id, "api-v03", api_action, event_label=api_label
        )
