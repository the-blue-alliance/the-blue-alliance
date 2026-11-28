from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional

from backend.common.helpers.pwa_url_helper import PwaUrlHelper
from backend.common.sitevars.platinum_sponsors import PlatinumSponsors, Sponsor


def render_time_context_processor() -> Dict[str, Optional[datetime]]:
    return dict(
        render_time=datetime.now(timezone.utc)
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


def platinum_sponsors_context_processor() -> Dict[str, Callable[[], List[Sponsor]]]:
    """
    Sponsors credited in the base.html footer. Passed as a callable so the
    sitevar is only read by templates that render the footer.
    """
    return dict(platinum_sponsors=lambda: PlatinumSponsors.sponsors())
