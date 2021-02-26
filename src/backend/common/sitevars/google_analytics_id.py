from typing_extensions import TypedDict

from backend.common.sitevars.base import SitevarBase


class ContentType(TypedDict):
    GOOGLE_ANALYTICS_ID: str


class GoogleAnalyticsID(SitevarBase[ContentType]):
    @staticmethod
    def key() -> str:
        return "google_analytics.id"

    @staticmethod
    def default_value() -> ContentType:
        return ContentType(
            GOOGLE_ANALYTICS_ID="",
        )

    @classmethod
    def google_analytics_id(cls) -> str:
        return cls.get().get("GOOGLE_ANALYTICS_ID", "")
