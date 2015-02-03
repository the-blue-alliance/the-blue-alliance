import calendar

from consts.notification_type import NotificationType
from notifications.base_notification import BaseNotification


class ScheduleUpdatedNotification(BaseNotification):

    def __init__(self, event):
        self.event = event

    def _build_dict(self):
        data = {}
        data['message_type'] = NotificationType.type_names[NotificationType.SCHEDULE_UPDATED]
        data['message_data'] = {}
        data['message_data']['event_key'] = self.event.key_name
        data['message_data']['event_name'] = self.event.name
        data['message_data']['first_match_time'] = calendar.timegm(self.event.matches[0].time.utctimetuple())
        return data
