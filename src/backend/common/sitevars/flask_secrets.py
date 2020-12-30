from typing_extensions import TypedDict

from backend.common.sitevars.base import SitevarBase


class ContentType(TypedDict):
    secret_key: str


class FlaskSecrets(SitevarBase[ContentType]):
    DEFAULT_SECRET_KEY: str = "thebluealliance"

    @staticmethod
    def key() -> str:
        return "flask.secrets"

    @staticmethod
    def default_value() -> ContentType:
        return ContentType(secret_key=FlaskSecrets.DEFAULT_SECRET_KEY)

    @classmethod
    def secret_key(cls) -> str:
        return cls.get().get("secret_key", FlaskSecrets.DEFAULT_SECRET_KEY)
