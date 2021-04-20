import base64
from typing import Optional

from typing_extensions import TypedDict

from backend.common.sitevars.base import SitevarBase


class ContentType(TypedDict):
    username: str
    authkey: str


class FMSAPISecrets(SitevarBase[ContentType]):
    @staticmethod
    def key() -> str:
        return "fmsapi.secrets"

    @staticmethod
    def default_value() -> ContentType:
        return ContentType(username="", authkey="")

    @classmethod
    def username(cls) -> Optional[str]:
        username = cls.get().get("username")
        return username if username else None  # Drop empty strings

    @classmethod
    def authkey(cls) -> Optional[str]:
        authkey = cls.get().get("authkey")
        return authkey if authkey else None  # Drop empty strings

    @classmethod
    def auth_token(cls) -> Optional[str]:
        """ The base64 encoded username + auth key - used to authenticate with the FMS API """

        username = cls.username()
        authkey = cls.authkey()
        if not username or not authkey:
            return None

        # py3 needs byte-strings for b64 - will convert back/forth from ascii for strings
        return base64.b64encode(
            "{}:{}".format(username, authkey).encode("ascii")
        ).decode("ascii")
