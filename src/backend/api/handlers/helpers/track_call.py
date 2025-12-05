from flask import g

from backend.common.google_analytics import GoogleAnalytics


def track_call_after_response(
    api_action: str, api_label: str | None = None, model_type: str | None = None
) -> None:
    """
    Schedules a callback to Google Analytics to track an API call.
    """
    # Save |auth_owner_id| and |auth_description| while we stil have access to the flask request context.
    auth_owner_id = g.auth_owner_id if hasattr(g, "auth_owner_id") else None
    auth_description = g.auth_description if hasattr(g, "auth_description") else None

    # Make sure auth_owner_id + auth_description are 1) not None and 2) strings
    if not isinstance(auth_owner_id, str) or not isinstance(auth_description, str):
        return

    if model_type is not None:
        api_action += f"/{model_type}"

    params = {
        "client_id": f"_{auth_owner_id}",  # Force this to be non-numeric so GA doesn't try to handle it as a number
        "owner_description": f"{auth_owner_id}:{auth_description}",
        "action": api_action,
        "label": api_label,
    }

    GoogleAnalytics.track_event(auth_owner_id, "api_v03", params, run_after=True)
