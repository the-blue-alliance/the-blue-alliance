from models.notifications.notification import Notification


class PingNotification(Notification):
    """ A ping - used to make sure a client/webhook can recieve notifications properly """

    _title = 'Test Notification'
    _body = 'This is a test message ensuring your device can recieve push messages from The Blue Alliance.'

    @classmethod
    def _type(cls):
        from consts.notification_type import NotificationType
        return NotificationType.PING

    @property
    def fcm_notification(self):
        from firebase_admin import messaging
        return messaging.Notification(
            title=self._title,
            body=self._body
        )

    @property
    def webhook_message_data(self):
        return {
            'title': self._title,
            'desc': self._body,
        }
