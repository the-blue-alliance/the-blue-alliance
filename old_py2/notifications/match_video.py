from consts.notification_type import NotificationType
from helpers.model_to_dict import ModelToDict
from notifications.base_notification import BaseNotification


class MatchVideoNotification(BaseNotification):
    def __init__(self, match):
        self.match = match
        self.event = match.event.get()

    @property
    def _type(self):
        return NotificationType.MATCH_VIDEO

    def _build_dict(self):
        data = {}
        data['notification_type'] = NotificationType.type_names[self._type]
        data['message_data'] = {}
        data['message_data']['event_name'] = self.event.name
        data['message_data']['match_key'] = self.match.key.id()
        data['message_data']['match'] = ModelToDict.matchConverter(self.match)
        return data


class EventMatchVideoNotification(BaseNotification):
    def __init__(self, match):
        self.match = match
        self.event = match.event.get()

    @property
    def _timeout(self):
        return 'EventMatchVideoNotification:{}'.format(self.event.key.id()), 60*10

    @property
    def _type(self):
        return NotificationType.EVENT_MATCH_VIDEO

    def _build_dict(self):
        data = {}
        data['notification_type'] = NotificationType.type_names[self._type]
        data['message_data'] = {}
        data['message_data']['event_key'] = self.event.key.id()
        data['message_data']['event_name'] = self.event.name
        return data
