from typing import Optional

from flask import g

from backend.common.google_analytics import GoogleAnalytics


def track_call_after_response(
    api_action: str, api_label: str, model_type: Optional[str] = None
) -> None:
    """
    Schedules a callback to Google Analytics to track an API call.
    """
    # Save |auth_owner_id| while we stil have access to the flask request context.
    auth_owner_id = g.auth_owner_id if hasattr(g, "auth_owner_id") else None
    if model_type is not None:
        api_action += f"/{model_type}"

    GoogleAnalytics.track_event(
        auth_owner_id, "api-v03", api_action, event_label=api_label, run_after=True
    )
