from typing_extensions import TypedDict

from backend.common.sitevars.base import SitevarBase


class ContentType(TypedDict):
    api_key: str


class GoogleApiSecret(SitevarBase[ContentType]):
    @staticmethod
    def key() -> str:
        return "google.secrets"

    @staticmethod
    def default_value() -> ContentType:
        return ContentType(api_key="")

    @classmethod
    def secret_key(cls) -> str:
        return cls.get().get("api_key", "")
