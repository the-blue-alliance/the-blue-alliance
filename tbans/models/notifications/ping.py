from tbans.models.notifications.notification import Notification


class PingNotification(Notification):
    """ A ping - used to make sure a client/webhook can recieve notifications properly """

    _title = 'Test Notification'
    _body = 'This is a test message ensuring your device can recieve push messages from The Blue Alliance.'

    @staticmethod
    def _type():
        from consts.notification_type import NotificationType
        return NotificationType.PING

    @property
    def notification_payload(self):
        from tbans.models.notifications.payloads.notification_payload import NotificationPayload
        return NotificationPayload(title=self._title, body=self._body)

    @property
    def webhook_payload(self):
        return {
            'title': self._title,
            'desc': self._body,
        }
