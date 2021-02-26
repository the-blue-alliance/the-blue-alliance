from typing_extensions import TypedDict

from backend.common.sitevars.base import SitevarBase


class ContentType(TypedDict):
    apiv3_key: str


class Apiv3Key(SitevarBase[ContentType]):
    @staticmethod
    def key() -> str:
        return "apiv3_key"

    @staticmethod
    def default_value() -> ContentType:
        return ContentType(
            apiv3_key="",
        )
