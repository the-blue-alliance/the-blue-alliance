from typing import TypedDict

from backend.common.sitevars.sitevar import Sitevar


class ContentType(TypedDict):
    apiv3_key: str


class Apiv3Key(Sitevar[ContentType]):
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
    def api_key(cls) -> str:
        return cls.get().get("apiv3_key", "")
