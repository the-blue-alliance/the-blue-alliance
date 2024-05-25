from typing import TypedDict

from backend.common.sitevars.sitevar import Sitevar


class ContentType(TypedDict):
    api_key: str


class LivestreamSecrets(Sitevar[ContentType]):
    @staticmethod
    def key() -> str:
        return "livestream.secrets"

    @staticmethod
    def description() -> str:
        return "For Livestream API"

    @staticmethod
    def default_value() -> ContentType:
        return ContentType(api_key="")
