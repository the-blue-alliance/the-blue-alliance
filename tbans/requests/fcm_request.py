from tbans.requests.request import Request


class FCMRequest(Request):
    """ Represents a notification payload and a delivery option to send to FCM.

    https://firebase.google.com/docs/reference/fcm/rest/v1/projects.messages

    Attributes:
        notification (Notification): The Notification to send.
        token (string): The FCM registration token to send a message to.
        topic (string): The FCM topic name to send a message to.
        condition (string): The topic condition to send a message.
    """

    def __init__(self, app, notification, token=None, topic=None, condition=None):
        """
        Note:
            Should only supply one delivery method - either token, topic, or connection.

        Args:
            app (firebase_admin.App): The Firebase app to send to.
            notification (Notification): The Notification to send.
            token (string): The FCM registration token to send a message to.
            topic (string): The FCM topic name to send a message to.
            condition (string): The topic condition to send a message.
        """
        super(FCMRequest, self).__init__(notification)

        import firebase_admin
        if not app or not isinstance(app, firebase_admin.App):
            raise ValueError('FCMRequest requires an app.')
        self._app = app

        # Ensure we've only passed one delivery option
        delivery_options = [x for x in [token, topic, condition] if x is not None]
        if len(delivery_options) == 0:
            raise TypeError('FCMRequest requires a delivery option - token, topic, or condition')
        elif len(delivery_options) > 1:
            raise TypeError('FCMRequest only accepts one delivery option - token, topic, or condition')

        # Ensure our delivery option looks right
        if not isinstance(delivery_options[0], basestring):
            raise ValueError('FCMRequest delivery option must be a string')

        self.token = token
        self.topic = topic
        self.condition = condition

    def __str__(self):
        if self.token:
            delivery_name = 'token'
            delivery_value = self.token
        elif self.topic:
            delivery_name = 'topic'
            delivery_value = self.topic
        elif self.condition:
            delivery_name = 'condition'
            delivery_value = self.condition

        return 'FCMRequest({}="{}", notification={})'.format(delivery_name, delivery_value, str(self.notification))

    def send(self):
        """ Attempt to send the notification.

        Returns:
            string: ID for the sent message.
        """
        from firebase_admin import messaging
        return messaging.send(self._fcm_message(), app=self._app)

    def _fcm_message(self):
        platform_config = self.notification.platform_config

        from tbans.consts.fcm.platform_type import PlatformType
        android_config = self.notification.android_config if self.notification.android_config \
            else platform_config and platform_config.platform_config(PlatformType.ANDROID)
        apns_config = self.notification.apns_config if self.notification.apns_config \
            else platform_config and platform_config.platform_config(PlatformType.APNS)
        webpush_config = self.notification.webpush_config if self.notification.webpush_config \
            else platform_config and platform_config.platform_config(PlatformType.WEBPUSH)
        # `platform_config and platform_config` is to short circuit execution if platform_config is None

        # Add `notification_type` to data payload
        data_payload = self.notification.data_payload if self.notification.data_payload else {}
        from consts.notification_type import NotificationType
        data_payload['notification_type'] = NotificationType.type_names[self.notification.__class__._type()]

        from firebase_admin import messaging
        return messaging.Message(
            data=data_payload,
            notification=self.notification.fcm_notification,
            android=android_config,
            webpush=webpush_config,
            apns=apns_config,
            token=self.token,
            topic=self.topic,
            condition=self.condition
        )
