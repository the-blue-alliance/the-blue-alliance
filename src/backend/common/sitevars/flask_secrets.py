from typing_extensions import TypedDict

from backend.common.sitevars.sitevar import Sitevar


class ContentType(TypedDict):
    secret_key: str


class FlaskSecrets(Sitevar[ContentType]):
    DEFAULT_SECRET_KEY: str = "thebluealliance"

    @staticmethod
    def key() -> str:
        return "flask.secrets"

    @staticmethod
    def description() -> str:
        return "Secret key for Flask session"

    @staticmethod
    def default_value() -> ContentType:
        return ContentType(secret_key=FlaskSecrets.DEFAULT_SECRET_KEY)

    @classmethod
    def secret_key(cls) -> str:
        secret_key = cls.get().get("secret_key")
        return secret_key if secret_key else FlaskSecrets.DEFAULT_SECRET_KEY
