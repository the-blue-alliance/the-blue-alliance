from typing import TypedDict

from backend.common.sitevars.sitevar import Sitevar


class ContentType(TypedDict):
    web: str
    android: str
    ios: str


class MobileClientIds(Sitevar[ContentType]):
    @staticmethod
    def key() -> str:
        return "mobile.clientIds"

    @staticmethod
    def description() -> str:
        return "For GCM Push & Authenticated API"

    @staticmethod
    def default_value() -> ContentType:
        return ContentType(web="", android="", ios="")
