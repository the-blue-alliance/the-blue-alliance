from models.notifications.notification import Notification


class AllianceSelectionNotification(Notification):

    def __init__(self, event):
        self.event = event

    @classmethod
    def _type(cls):
        from consts.notification_type import NotificationType
        return NotificationType.ALLIANCE_SELECTION

    @property
    def fcm_notification(self):
        from firebase_admin import messaging
        return messaging.Notification(
            title='{} Alliances Updated'.format(self.event.event_short.upper()),
            body='{} alliances have been updated.'.format(self.event.normalized_name)
        )

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
