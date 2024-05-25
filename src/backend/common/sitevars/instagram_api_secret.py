from typing import TypedDict

from backend.common.sitevars.sitevar import Sitevar


class ContentType(TypedDict):
    api_key: str


class InstagramApiSecret(Sitevar[ContentType]):
    @staticmethod
    def key() -> str:
        return "instagram.secrets"

    @staticmethod
    def description() -> str:
        return "For Instagram embed API Calls"

    @staticmethod
    def default_value() -> ContentType:
        return ContentType(api_key="")
