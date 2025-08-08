from typing import Optional, TypedDict

from backend.common.sitevars.sitevar import Sitevar


class ContentType(TypedDict):
    GOOGLE_ANALYTICS_ID: str
    API_SECRET: str


class GoogleAnalyticsID(Sitevar[ContentType]):
    @staticmethod
    def key() -> str:
        return "google_analytics.id"

    @staticmethod
    def description() -> str:
        return "Google Analytics ID and API secret for logging API requests"

    @staticmethod
    def default_value() -> ContentType:
        return ContentType(
            GOOGLE_ANALYTICS_ID="",
            API_SECRET="",
        )

    @classmethod
    def google_analytics_id(cls) -> Optional[str]:
        google_analytics_id = cls.get().get("GOOGLE_ANALYTICS_ID")
        return (
            google_analytics_id if google_analytics_id else None
        )  # Drop empty strings

    @classmethod
    def api_secret(cls) -> Optional[str]:
        api_secret = cls.get().get("API_SECRET")
        return api_secret if api_secret else None  # Drop empty strings
