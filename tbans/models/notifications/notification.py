class Notification(object):
    """
    Base notification classs - represents message, data, and platform config payloads for notifications.
    """
    def __str__(self):
        values = [ value for value in
            [(self.data_payload, 'data_payload'),
            (self.fcm_notification and "\"{}\"".format(self.fcm_notification.title), 'fcm_notification.title'),
            (self.fcm_notification and "\"{}\"".format(self.fcm_notification.body), 'fcm_notification.body'),
            (self.platform_config, 'platform_config'),
            (self.android_config, 'android_config'),
            (self.apns_config and self.apns_config.headers, 'apns_config'),
            (self.webpush_config and self.webpush_config.headers, 'webpush_config'),
            (self.webhook_message_data, 'webhook_message_data')] + self._additional_logging_values()
            if value[0] is not None
        ]
        value_strings = ['{}={}'.format(str(value[1]), str(value[0])) for value in values]
        value_string = ' '.join(value_strings)
        return '{}({})'.format(self.__class__.__name__, value_string)

    @classmethod
    def _type(cls):
        """ Corresponding NotificationType for this notification

        Returns:
            NotificationType constant
         """
        raise NotImplementedError("Notification subclass must implement type")

    @property
    def fcm_notification(self):
        """ FCM Notification object to use for FCM.

        Returns:
            firebase_admin.messaging.Notification: None if no notification.
        """
        return None

    @property
    def data_payload(self):
        """ Arbitrary key/value payload.

        Returns:
            dictionary, or None if no data payload.
        """
        return None

    @property
    def platform_config(self):
        """ Default config to use for all platforms.

        Note:
            If you implement android_config, apns_config, or webpush_config,
            those values will be used for their specific platforms instead of this one.

        Returns:
            tbans.models.fcm.PlatformConfig: None if no platform config is necessary.
        """
        return None

    @property
    def android_config(self):
        """ Android specific options for messages sent through FCM connection server.

        Returns:
            firebase_admin.messaging.AndroidConfig: None if no Android-specific config is necessary.
        """
        return None

    @property
    def apns_config(self):
        """ Apple Push Notification Service specific options for messages sent through FCM connection server.

        Returns:
            firebase_admin.messaging.ApnsConfig: None if no APNS-specific config is necessary.
        """
        return None

    @property
    def webpush_config(self):
        """ Webpush protocol options for messages sent through FCM connection server.

        Returns:
            firebase_admin.messaging.WebpushConfig: None if no webpush-specific config is necessary.
        """
        return None

    @property
    def webhook_message_data(self):
        """ `message_data` dictionary for a webhook request.

        Note:
            By default, will fall back to using the data_payload.

        Returns:
            dictionary: None if no webhook data payload.
        """
        return self.data_payload

    def _additional_logging_values(self):
        """ Return a list of value (or None)/name tuples to be adding to str for logging """
        return []
