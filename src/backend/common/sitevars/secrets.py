from typing_extensions import TypedDict

from backend.common.sitevars.base import SitevarBase


class ContentType(TypedDict):
    secret_key: str


class Secrets(SitevarBase[ContentType]):
    DEFAULT_SECRET_KEY: str = "thebluealliance"

    @staticmethod
    def key() -> str:
        return "secrets"

    @staticmethod
    def default_value() -> ContentType:
        return ContentType(secret_key=Secrets.DEFAULT_SECRET_KEY)

    @classmethod
    def secret_key(cls) -> str:
        return cls.get().get("secret_key", Secrets.DEFAULT_SECRET_KEY)
