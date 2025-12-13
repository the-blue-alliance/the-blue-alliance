from typing import Optional, TypedDict

from backend.common.sitevars.sitevar import Sitevar


class ContentType(TypedDict):
    url_format: str


class RegionalAdvancementApiSecret(Sitevar[ContentType]):
    @staticmethod
    def key() -> str:
        return "ra_api.secrets"

    @staticmethod
    def default_value():
        return ContentType(url_format="")

    @staticmethod
    def description():
        return "For accessing regional advancement info"

    @classmethod
    def url_format(cls) -> Optional[str]:
        fmt = cls.get().get("url_format")
        return fmt if fmt else None
