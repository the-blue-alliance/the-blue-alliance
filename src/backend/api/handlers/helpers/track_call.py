from typing import Optional

from flask import g

from backend.common.google_analytics import GoogleAnalytics


def track_call_after_response(
    api_action: str, api_label: Optional[str] = None, model_type: Optional[str] = None
) -> None:
    """
    Schedules a callback to Google Analytics to track an API call.
    """
    # Save |auth_owner_id| while we stil have access to the flask request context.
    auth_owner_id = g.auth_owner_id if hasattr(g, "auth_owner_id") else None
    if model_type is not None:
        api_action += f"/{model_type}"

    params = {
        "client_id": str(auth_owner_id),
        "action": api_action,
        "label": api_label,
    }

    GoogleAnalytics.track_event(auth_owner_id, "api_v03", params, run_after=True)
