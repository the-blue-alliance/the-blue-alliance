import datetime

from consts.notification_type import NotificationType
from notifications.base_notification import BaseNotification


class UpcomingMatchNotification(BaseNotification):

    def __init__(self, match, event):
        self.match = match
        self.event = event

    def _build_dict(self):
        data = {}
        data['message_type'] = NotificationType.type_names[NotificationType.UPCOMING_MATCH]
        data['message_data'] = {}
        data['message_data']['event_name'] = self.event.name
        data['message_data']['match_key'] = self.match.key_name
        data['message_data']['team_keys'] = self.match.team_key_names
        data['message_data']['scheduled_time'] = self.match.time
        data['message_data']['predicted_time'] = self.match.time  # TODO Add in some time predictions
        return data
