from typing import Optional

from backend.common.consts.suggestion_type import SuggestionType
from backend.common.environment import Environment

# The PWA is served at beta.thebluealliance.com in production (see
# src/dispatch.yaml). Locally it runs on the vite dev server.
BETA_BASE_URL = "https://beta.thebluealliance.com"
LOCAL_PWA_BASE_URL = "http://localhost:5173"
# The Jinja site, for links in prod-only messages (emails, Slack)
WWW_BASE_URL = "https://www.thebluealliance.com"


class PwaUrlHelper:
    """
    Builds links into the PWA for pages that no longer exist on the Jinja
    web service, such as the moderator suggestion review UI.
    """

    @staticmethod
    def base_url() -> str:
        # Local dev must never bounce a developer to production
        if Environment.is_dev():
            return LOCAL_PWA_BASE_URL
        return BETA_BASE_URL

    @classmethod
    def suggestion_review_url(
        cls, suggestion_type: Optional[SuggestionType] = None
    ) -> str:
        url = f"{cls.base_url()}/suggest/review"
        if suggestion_type is not None:
            url = f"{url}/{suggestion_type.value}"
        return url
