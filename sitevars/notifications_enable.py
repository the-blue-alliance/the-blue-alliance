import json

from models.sitevar import Sitevar


class NotificationsEnable:

    @staticmethod
    def _default_sitevar():
        return Sitevar.get_or_insert('notifications.enable', values_json=json.dumps(True))

    @staticmethod
    def notifications_enabled():
        notifications = NotificationsEnable._default_sitevar()
        return notifications.contents

    @staticmethod
    def enable_notifications(enable):
        notifications = NotificationsEnable._default_sitevar()
        notifications.contents = enable
        notifications.put()
