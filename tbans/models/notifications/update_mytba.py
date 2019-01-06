from tbans.models.notifications.notification import Notification
from tbans.models.notifications.payloads.platform_payload import PlatformPayload


# Base notification class for myTBA update models
class UpdateMyTBANotification(Notification):
    """ Base notification class for myTBA update notifications - ex: favorites and subscriptions

    Attributes:
        type_name (string): Human readable string that represents the type for this notification (ex: 'favorite')
        user_id (string): User/account ID that we're sending notifications for - used for collapse key.
        sending_device_key (string): The FCM token for the device that triggered the notification.
    """

    def __init__(self, type_name, user_id, sending_device_key):
        """
        Args:
            type_name (string): Human readable string that represents the type for this notification (ex: 'favorite')
            user_id (string): User/account ID that we're sending notifications for - used for collapse key.
            sending_device_key (string): The FCM token for the device that triggered the notification.
        """
        # Check type_name, user_id, and sending_device_key
        for (value, name) in [(type_name, 'type_name'), (user_id, 'user_id'), (sending_device_key, 'sending_device_key')]:
            # Make sure our value exists
            if value is None:
                raise ValueError('UpdateMyTBANotification requires a {}'.format(name))
            # Check that our value looks right
            if not isinstance(value, basestring):
                raise TypeError('UpdateMyTBANotification {} must be an string'.format(name))

        self.type_name = type_name
        self.user_id = user_id
        self.sending_device_key = sending_device_key

    @property
    def data_payload(self):
        return {
            'sending_device_key': self.sending_device_key
        }

    @property
    def webhook_payload(self):
        # Don't send `sending_device_key` to webhooks
        return None

    @property
    def platform_payload(self):
        return PlatformPayload(collapse_key='{}_{}_update'.format(self.user_id, self.type_name))

    def _additional_logging_values(self):
        return [(self.type_name, 'type_name'), (self.user_id, 'user_id'), (self.sending_device_key, 'sending_device_key')]
