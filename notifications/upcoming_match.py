import calendar
import datetime

from consts.notification_type import NotificationType
from notifications.base_notification import BaseNotification


class UpcomingMatchNotification(BaseNotification):

    def __init__(self, match, event):
        self.match = match
        self.event = event

    @property
    def _type(self):
        return NotificationType.UPCOMING_MATCH

    def _build_dict(self):
        data = {}
        data['message_type'] = NotificationType.type_names[self._type]
        data['message_data'] = {}
        data['message_data']['event_name'] = self.event.name
        data['message_data']['match_key'] = self.match.key_name
        data['message_data']['team_keys'] = self.match.team_key_names
        if self.match.time:
            data['message_data']['scheduled_time'] = calendar.timegm(self.match.time.utctimetuple())
            data['message_data']['predicted_time'] = calendar.timegm(self.match.time.utctimetuple())  # TODO Add in some time predictions
        else:
            data['message_data']['scheduled_time'] = None
            data['message_data']['predicted_time'] = None

        return data
