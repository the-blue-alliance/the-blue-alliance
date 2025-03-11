from typing import Optional, TypedDict

from backend.common.sitevars.sitevar import Sitevar


class ContentType(TypedDict):
    api_secret: str


class NexusApiSecrets(Sitevar[ContentType]):
    @staticmethod
    def key() -> str:
        return "nexus.secrets"

    @staticmethod
    def default_value():
        return ContentType(api_secret="")

    @staticmethod
    def description():
        return "For accessing the Nexus API"

    @classmethod
    def secret(cls) -> Optional[str]:
        secret = cls.get().get("api_secret")
        return secret if secret else None  # drop empty strings
