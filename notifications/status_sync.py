from consts.notification_type import NotificationType
from notifications.base_notification import BaseNotification


class StatusSyncNotification(BaseNotification):

    _track_call = False
    _push_firebase = False

    @property
    def _type(self):
        return NotificationType.STATUS_SYNC

    def _build_dict(self):
        return {}
