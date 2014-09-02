from consts.client_type import ClientType
from consts.notification_type import NotificationType
from controllers.gcm.gcm import GCMMessage
from helpers.model_to_dict import ModelToDict
from notifications.base_notification import BaseNotification


class MatchScoreNotification(BaseNotification):

    def __init__(self, match):
        self.match = match

    def _build_dict(self):
        data = {}
        data['message_type'] = NotificationType.type_names[NotificationType.MATCH_SCORE]
        data['message_data'] = {}
        data['message_data']['event_name'] = self.match.event.get().name
        data['message_data']['match'] = ModelToDict.matchConverter(self.match)
        return data

    def _render_android(self):
        gcm_keys = self.keys[ClientType.OS_ANDROID]

        data = self._build_dict()

        return GCMMessage(gcm_keys, data)
