from tbans.models.notifications.notification import Notification


class AllianceSelectionNotification(Notification):

    def __init__(self, event):
        self.event = event
        self._event_feed = event.key_name
        self._district_feed = event.event_district_abbrev

    @classmethod
    def _type(cls):
        from tba.consts.notification_type import NotificationType
        return NotificationType.ALLIANCE_SELECTION

    @property
    def fcm_notification(self):
        from firebase_admin import messaging
        return messaging.Notification(
            title='{} Alliances Updated'.format(self.event.event_short.upper()),
            body='{} alliances have been updated.'.format(self.event.normalized_name)
        )

    @property
    def platform_config(self):
        from tbans.consts.fcm.platform_priority import PlatformPriority
        from tbans.models.fcm.platform_config import PlatformConfig
        return PlatformConfig(priority=PlatformPriority.HIGH)

    @property
    def data_payload(self):
        from helpers.model_to_dict import ModelToDict
        return {
            'event': ModelToDict.eventConverter(self.event),
            'event_key': self.event.key_name
        }

    @property
    def webhook_message_data(self):
        payload = self.data_payload
        payload['event_name'] = self.event.name
        return payload
