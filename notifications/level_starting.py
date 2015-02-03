import calendar

from consts.notification_type import NotificationType
from notifications.base_notification import BaseNotification


class CompLevelStartingNotification(BaseNotification):

    def __init__(self, match, event):
        self.match = match
        self.event = event

    def _build_dict(self):
        data = {}
        data['message_type'] = NotificationType.type_names[NotificationType.LEVEL_STARTING]
        data['message_data'] = {}
        data['message_data']['event_name'] = self.event.name
        data['message_data']['event_key'] = self.event.key_name
        data['message_data']['comp_level'] = self.match.comp_level
        if self.match.time:
            data['message_data']['scheduled_time'] = calendar.timegm(self.match.time.utctimetuple())
        else:
            data['message_data']['scheduled_time'] = None

        return data
