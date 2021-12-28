from backend.common.sitevars.sitevar import Sitevar


class ApiStatusFMSApiDown(Sitevar[bool]):
    @staticmethod
    def key() -> str:
        return "apistatus.fmsapi_down"

    @staticmethod
    def description() -> str:
        return "Is FMSAPI down?"

    @staticmethod
    def default_value() -> bool:
        return False

    @classmethod
    def set_down(cls, down: bool) -> None:
        cls.update(
            should_update=lambda v: v is not down,
            update_f=lambda _: down,
        )
