from datetime import datetime, timezone
from typing import Dict, Optional

from backend.common.helpers.pwa_url_helper import PwaUrlHelper


def render_time_context_processor() -> Dict[str, Optional[datetime]]:
    return dict(
        render_time=datetime.now(timezone.utc)  # pyre-ignore[16]
        .astimezone(timezone.utc)
        .replace(second=0, microsecond=0)
    )  # Prevent ETag from changing too quickly


def pwa_url_context_processor() -> Dict[str, str]:
    """
    Links from Jinja pages into the PWA, for features that have moved there
    (the moderator suggestion review UI). Env-aware so local dev never links
    to production.
    """
    return dict(
        pwa_base_url=PwaUrlHelper.base_url(),
        pwa_suggestion_review_url=PwaUrlHelper.suggestion_review_url(),
    )
