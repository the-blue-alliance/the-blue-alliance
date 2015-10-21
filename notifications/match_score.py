from consts.notification_type import NotificationType
from helpers.model_to_dict import ModelToDict
from notifications.base_notification import BaseNotification


class MatchScoreNotification(BaseNotification):

    def __init__(self, match):
        self.match = match
        self._event_feed = match.event.id
        # TODO Add notion of District to Match model?

    @property
    def _type(self):
        return NotificationType.MATCH_SCORE

    def _build_dict(self):
        data = {}
        data['message_type'] = NotificationType.type_names[self._type]
        data['message_data'] = {}
        data['message_data']['event_name'] = self.match.event.get().name
        data['message_data']['match'] = ModelToDict.matchConverter(self.match)
        return data
