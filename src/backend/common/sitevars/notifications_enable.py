from backend.common.sitevars.base import SitevarBase


class NotificationsEnable(SitevarBase[bool]):
    @staticmethod
    def key() -> str:
        return "notifications.enable"

    @staticmethod
    def default_value() -> bool:
        return True

    @classmethod
    def notifications_enabled(cls) -> bool:
        return cls.get()

    @classmethod
    def enable_notifications(cls, enable: bool):
        cls.update(
            should_update=lambda v: v != enable, update_f=lambda _: enable,
        )
