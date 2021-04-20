from typing import Optional

from typing_extensions import TypedDict

from backend.common.sitevars.sitevar_base import SitevarBase


class ContentType(TypedDict):
    api_key: str


class GoogleApiSecret(SitevarBase[ContentType]):
    @staticmethod
    def key() -> str:
        return "google.secrets"

    @staticmethod
    def description() -> str:
        return "For Google API Calls"

    @staticmethod
    def default_value() -> ContentType:
        return ContentType(api_key="")

    @classmethod
    def secret_key(cls) -> Optional[str]:
        secret_key = cls.get().get("api_key")
        return secret_key if secret_key else None  # Drop empty strings
