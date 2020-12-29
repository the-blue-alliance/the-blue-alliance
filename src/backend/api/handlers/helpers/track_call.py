from flask import g

from backend.common.google_analytics import GoogleAnalytics
from backend.common.run_after_response import run_after_response


def track_call_after_response(api_action: str, api_label: str) -> None:
    auth_owner_id = g.api_auth_access.owner.id() if g.api_auth_access.owner else None

    @run_after_response
    def track_call():
        GoogleAnalytics.track_event(
            auth_owner_id, "api-v03", api_action, event_label=api_label
        )
