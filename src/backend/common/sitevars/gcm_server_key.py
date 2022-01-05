from typing import TypedDict

from backend.common.sitevars.sitevar import Sitevar


class ContentType(TypedDict):
    gcm_key: str


class GcmServerKey(Sitevar[ContentType]):
    @staticmethod
    def key() -> str:
        return "gcm.serverKey"

    @staticmethod
    def description() -> str:
        return "For GCM Push"

    @staticmethod
    def default_value() -> ContentType:
        return ContentType(gcm_key="")
