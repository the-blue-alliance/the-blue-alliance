from backend.common.sitevars.sitevar_base import SitevarBase


class ApiStatusFMSApiDown(SitevarBase[bool]):
    @staticmethod
    def key() -> str:
        return "apistatus.fmsapi_down"

    @staticmethod
    def description() -> str:
        return "Is FMSAPI down?"

    @staticmethod
    def default_value() -> bool:
        return False
