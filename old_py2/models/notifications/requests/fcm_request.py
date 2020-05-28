from firebase_admin import messaging

from models.notifications.requests.request import Request

# Fix positional argument warnings - can remove once we upgrade to firebase-admin=4.0.0
from googleapiclient import _helpers
_helpers.positional_parameters_enforcement = _helpers.POSITIONAL_IGNORE


MAXIMUM_TOKENS = 500


class FCMRequest(Request):
    """ Represents a notification payload and a delivery option to send to FCM.
    https://firebase.google.com/docs/reference/fcm/rest/v1/projects.messages
    Attributes:
        notification (Notification): The Notification to send.
        tokens (list, string): The FCM registration tokens (up to 100) to send a message to.
    """

    def __init__(self, app, notification, tokens=None):
        """
        Note:
            Should only supply one delivery method - either token, topic, or connection.
        Args:
            app (firebase_admin.App): The Firebase app to send to.
            notification (Notification): The Notification to send.
            tokens (list, string): The FCM registration tokens (up to 100) to send a message to.
        """
        super(FCMRequest, self).__init__(notification=notification)

        self._app = app

        if len(tokens) > MAXIMUM_TOKENS:
            raise ValueError('FCMRequest tokens must contain less than {} tokens'.format(MAXIMUM_TOKENS))

        self.tokens = tokens

    def __str__(self):
        return 'FCMRequest(tokens={}, notification={})'.format(self.tokens, str(self.notification))

    def send(self):
        """ Attempt to send the notification.
        Returns:
            messaging.BatchResponse - Batch response object for the messages sent.
        """
        response = messaging.send_multicast(self._fcm_message(), app=self._app)
        if response.success_count > 0:
            self.defer_track_notification(response.success_count)
        return response

    def _fcm_message(self):
        platform_config = self.notification.platform_config

        from consts.fcm.platform_type import PlatformType
        android_config = self.notification.android_config if self.notification.android_config \
            else platform_config and platform_config.platform_config(platform_type=PlatformType.ANDROID)
        apns_config = self.notification.apns_config if self.notification.apns_config \
            else platform_config and platform_config.platform_config(platform_type=PlatformType.APNS)
        webpush_config = self.notification.webpush_config if self.notification.webpush_config \
            else platform_config and platform_config.platform_config(platform_type=PlatformType.WEBPUSH)
        # `platform_config and platform_config` is to short circuit execution if platform_config is None

        # Additional APNS-specific configuration - make sure we have some payload
        if not apns_config:
            apns_config = messaging.APNSConfig()
        if not apns_config.payload:
            apns_config.payload = messaging.APNSPayload(aps=messaging.Aps())

        if self.notification.fcm_notification:
            # Set sound
            apns_config.payload.aps.sound = 'default'
        else:
            # Set content_available
            apns_config.payload.aps.content_available = True

        # Add `notification_type` to data payload
        data_payload = self.notification.data_payload if self.notification.data_payload else {}
        # Remove `None` from data payload, since FCM won't accept them
        data_payload = {k: v for k, v in data_payload.items() if v is not None}
        from consts.notification_type import NotificationType
        data_payload['notification_type'] = NotificationType.type_names[self.notification.__class__._type()]

        return messaging.MulticastMessage(
            tokens=self.tokens,
            data=data_payload,
            notification=self.notification.fcm_notification,
            android=android_config,
            webpush=webpush_config,
            apns=apns_config
        )
