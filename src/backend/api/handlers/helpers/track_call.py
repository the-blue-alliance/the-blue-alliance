from typing import Optional

from flask import g

from backend.common.google_analytics import GoogleAnalytics
from backend.common.run_after_response import run_after_response


def track_call_after_response(
    api_action: str, api_label: str, model_type: Optional[str] = None
) -> None:
    """
    Schedules a callback to Google Analytics to track an API call.
    """
    # Save |auth_owner_id| whiel we stil have access to the flask request context.
    auth_owner_id = g.auth_owner_id if g.auth_owner_id else None
    if model_type is not None:
        api_action += f"/{model_type}"

    @run_after_response
    def track_call():
        GoogleAnalytics.track_event(
            auth_owner_id, "api-v03", api_action, event_label=api_label
        )
