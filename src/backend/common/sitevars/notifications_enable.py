import json

from backend.common.models.sitevar import Sitevar


class NotificationsEnable:
    @staticmethod
    def _default_sitevar() -> Sitevar:
        return Sitevar.get_or_insert(
            "notifications.enable", values_json=json.dumps(True)
        )

    @staticmethod
    def notifications_enabled() -> bool:
        notifications = NotificationsEnable._default_sitevar()
        return notifications.contents

    @staticmethod
    def enable_notifications(enable: bool):
        notifications = NotificationsEnable._default_sitevar()
        notifications.contents = enable
        notifications.put()
