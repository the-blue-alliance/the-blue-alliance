from typing import Optional, TypedDict

from backend.common.sitevars.sitevar import Sitevar


class ContentType(TypedDict):
    api_key: str
    api_secret: str


class SmugmugApiSecret(Sitevar[ContentType]):
    @staticmethod
    def key() -> str:
        return "smugmug.secrets"

    @staticmethod
    def description() -> str:
        return "For SmugMug API Calls"

    @staticmethod
    def default_value() -> ContentType:
        return ContentType(api_key="", api_secret="")

    @classmethod
    def api_key(cls) -> Optional[str]:
        api_key = cls.get().get("api_key")
        return api_key if api_key else None  # Drop empty strings
