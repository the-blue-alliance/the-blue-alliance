
class Notification(object):

    """
    Base notification classs - represents message, data, and platform config payloads for notifications
    """

    def __str__(self):
        values = [ value for value in
            [(self.data_payload, 'data_payload'),
            (self.notification_payload, 'notification_payload'),
            (self.platform_payload, 'platform_payload'),
            (self.android_payload, 'android_payload'),
            (self.apns_payload, 'apns_payload'),
            (self.webpush_payload, 'webpush_payload'),
            (self.webhook_payload, 'webhook_payload')] + self._additional_logging_values()
            if value[0] is not None
        ]
        value_strings = ['{}={}'.format(str(value[1]), str(value[0])) for value in values]
        value_string = ' '.join(value_strings)
        return '{}({})'.format(self.__class__.__name__, value_string)

    @staticmethod
    def _type():
        """ Corresponding NotificationType for this notification

        Returns:
            NotificationType constant
         """
        raise NotImplementedError("Notification subclass must implement type")

    @property
    def data_payload(self):
        """ Arbitrary key/value payload

        Returns:
            dictionary, or None if no data payload
        """
        return None

    @property
    def notification_payload(self):
        """ Basic notification template to use across all platforms

        Returns:
            NotificationPayload: None if no notification payload.
        """
        return None

    @property
    def platform_payload(self):
        """ Default payload to use for all platforms

        Note:
            If you implement android_payload, apns_payload, or webpush_payload,
            those values will be used for their specific platforms instead of this one

        Returns:
            PlatformPayload: None if no platform config is necessary.
        """
        return None

    @property
    def android_payload(self):
        """ Android specific options for messages sent through FCM connection server

        Note:
            Should return a PlatformPayload with platform_type = PlatformPayloadType.ANDROID

        Returns:
            PlatformPayload: None if no Android-specific config is necessary.
        """
        return None

    @property
    def apns_payload(self):
        """ Apple Push Notification Service specific options

        Note:
            Should return a PlatformPayload with platform_type = PlatformPayloadType.APNS

        Returns:
            PlatformPayload: None if no APNS-specific config is necessary.
        """
        return None

    @property
    def webpush_payload(self):
        """ Webpush protocol options

        Note:
            Should return a PlatformPayload with platform_type = PlatformPayloadType.WEBPUSH

        Returns:
            PlatformPayload: None if no webpush-specific config is necessary.
        """
        return None

    @property
    def webhook_payload(self):
        """ `message_data` dictionary for a webhook request

        Note:
            By default, will fall back to using the data_payload

        Returns:
            dictionary: None if no webhook data payload.
        """
        return self.data_payload

    def _additional_logging_values(self):
        """ Return a list of value (or None)/name tuples to be adding to str for logging """
        return []
