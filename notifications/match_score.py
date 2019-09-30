from consts.notification_type import NotificationType
from helpers.model_to_dict import ModelToDict
from notifications.base_notification import BaseNotification


class MatchScoreNotification(BaseNotification):

    _priority = 'high'

    def __init__(self, match):
        self.match = match
        self.event = match.event.get()

    @property
    def _type(self):
        return NotificationType.MATCH_SCORE

    def _build_dict(self):
        data = {}
        data['notification_type'] = NotificationType.type_names[self._type]
        data['message_data'] = {}
        data['message_data']['event_name'] = self.event.name
        data['message_data']['event_key'] = self.event.key_name
        data['message_data']['match'] = ModelToDict.matchConverter(self.match)
        return data
