from typing import Optional

from typing_extensions import TypedDict

from backend.common.sitevars.sitevar_base import SitevarBase


class ContentType(TypedDict):
    apiv3_key: str


class Apiv3Key(SitevarBase[ContentType]):
    @staticmethod
    def key() -> str:
        return "apiv3_key"

    @staticmethod
    def description() -> str:
        return "APIv3 key"

    @staticmethod
    def default_value() -> ContentType:
        return ContentType(
            apiv3_key="",
        )

    @classmethod
    def api_key(cls) -> Optional[str]:
        api_key = cls.get().get("apiv3_key")
        return api_key if api_key else None  # Drop empty strings
