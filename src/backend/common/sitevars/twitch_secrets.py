from typing import TypedDict

from backend.common.sitevars.sitevar import Sitevar


class ContentType(TypedDict):
    client_id: str
    client_secret: str


class TwitchSecrets(Sitevar[ContentType]):
    @staticmethod
    def key() -> str:
        return "twitch.secrets"

    @staticmethod
    def description() -> str:
        return "For Twitch API"

    @staticmethod
    def default_value() -> ContentType:
        return ContentType(client_id="", client_secret="")

    @classmethod
    def client_id(cls) -> str:
        return cls.get()["client_id"]

    @classmethod
    def client_secret(cls) -> str:
        return cls.get()["client_secret"]
