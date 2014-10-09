from consts.notification_type import NotificationType
from notifications.base_notification import BaseNotification


class SchedulePostedNotification(BaseNotification):

    def __init__(self, event):
        self.event = event

    def _build_dict(self):
        data = {}
        data['message_type'] = NotificationType.type_names[NotificationType.SCHEDULE_POSTED]
        data['message_data'] = {}
        data['message_data']['event_key'] = self.event.key_name
        data['message_data']['event_name'] = self.event.name
        data['message_data']['first_match_time'] = self.event.matches[0].time
        return data
