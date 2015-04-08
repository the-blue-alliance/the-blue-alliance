import calendar

from consts.notification_type import NotificationType
from notifications.base_notification import BaseNotification


class ScheduleUpdatedNotification(BaseNotification):

    def __init__(self, event):
        self.event = event

    @property
    def _type(self):
        return NotificationType.SCHEDULE_UPDATED

    def _build_dict(self):
        data = {}
        data['message_type'] = NotificationType.type_names[self._type]
        data['message_data'] = {}
        data['message_data']['event_key'] = self.event.key_name
        data['message_data']['event_name'] = self.event.name
        if self.event.matches[0] and self.event.matches[0].time:
            data['message_data']['first_match_time'] = calendar.timegm(self.event.matches[0].time.utctimetuple())
        else:
            data['message_data']['first_match_time'] = None

        return data
