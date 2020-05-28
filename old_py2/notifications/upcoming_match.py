import calendar
import datetime

from consts.notification_type import NotificationType
from helpers.webcast_online_helper import WebcastOnlineHelper
from notifications.base_notification import BaseNotification


class UpcomingMatchNotification(BaseNotification):

    _priority = 'high'

    def __init__(self, match, event):
        self.match = match
        self.event = event

    @property
    def _type(self):
        return NotificationType.UPCOMING_MATCH

    def _build_dict(self):
        data = {}
        data['notification_type'] = NotificationType.type_names[self._type]
        data['message_data'] = {}
        data['message_data']['event_key'] = self.event.key_name
        data['message_data']['event_name'] = self.event.name
        data['message_data']['match_key'] = self.match.key_name
        data['message_data']['team_keys'] = self.match.team_key_names

        if self.match.time:
            data['message_data']['scheduled_time'] = calendar.timegm(self.match.time.utctimetuple())
        else:
            data['message_data']['scheduled_time'] = None

        if self.match.predicted_time:
            data['message_data']['predicted_time'] = calendar.timegm(self.match.predicted_time.utctimetuple())
        else:
            data['message_data']['predicted_time'] = None

        current_webcasts = self.event.current_webcasts
        WebcastOnlineHelper.add_online_status(current_webcasts)
        online_webcasts = filter(lambda x: x.get('status', '') != 'offline', current_webcasts if current_webcasts else [])
        if online_webcasts:
            data['message_data']['webcast'] = online_webcasts[0]
        else:
            data['message_data']['webcast'] = None

        return data
