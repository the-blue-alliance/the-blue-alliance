from typing import Dict, Set

from backend.common.consts.auth_type import AuthType
from backend.common.sitevars.sitevar import Sitevar


ContentType = Dict[str, bool]


class TrustedApiConfig(Sitevar[ContentType]):
    """
    Keys in the dict are the stringified int value of an AuthType
    """

    @staticmethod
    def key() -> str:
        return "trustedapi"

    @staticmethod
    def description() -> str:
        return "For configuring which types of event data are allowed to be changed via the trusted API"

    @staticmethod
    def default_value() -> Dict[str, bool]:
        return {}

    @classmethod
    def is_auth_enalbed(cls, required_auth_types: Set[AuthType]) -> bool:
        config = cls.get()
        return all(
            # Allow access to the trusted API if unset
            config.get(str(auth_type), True)
            for auth_type in required_auth_types
        )
