from consts.notification_type import NotificationType
from notifications.base_notification import BaseNotification


class EventDownNotification(BaseNotification):

    _track_call = False
    _push_firebase = False

    def __init__(self, event_key, event_name):
        self.event_key = event_key
        self.event_name = event_name

    @property
    def _type(self):
        return NotificationType.EVENT_DOWN

    def _build_dict(self):
        data = {
            "event_key": self.event_key,
            "event_name": self.event_name
        }
        return data
