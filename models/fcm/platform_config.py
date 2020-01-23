from consts.fcm.platform_priority import PlatformPriority


class PlatformConfig(object):
    """
    Represents platform-specific push notification configuration options.

    https://firebase.google.com/docs/reference/fcm/rest/v1/projects.messages

    Args:
        collapse_key (string): Collapse key for push notification - may be None.
        priority (int): Priority for push notification - may be None.
    """
    # TODO: Add ttl
    def __init__(self, collapse_key=None, priority=None):
        """
        Args:
            collapse_key (string): Collapse key for push notification - may be None.
            priority (int): Priority for push notification - may be None.
        """
        self.collapse_key = collapse_key

        # Check that our priority looks right
        if priority:
            PlatformPriority.validate(priority)
        self.priority = priority

    def __str__(self):
        return 'PlatformConfig(collapse_key="{}" priority={})'.format(self.collapse_key, self.priority)

    def platform_config(self, platform_type):
        """ Return a platform-specific configuration object for a platform_type, given the platform payload.

        Args:
            platform_type (PlatformType): Type for the platform config.

        Returns:
            object: Either a AndroidConfig, ApnsConfig, or WebpushConfig depending on the platform_type.
        """
        from consts.fcm.platform_type import PlatformType
        # Validate that platform_type is supported
        PlatformType.validate(platform_type)

        from firebase_admin import messaging
        if platform_type == PlatformType.ANDROID:
            priority = PlatformPriority.platform_priority(platform_type, self.priority) \
                if self.priority is not None else None

            return messaging.AndroidConfig(
                collapse_key=self.collapse_key,
                priority=priority
            )
        else:
            headers = {}

            if self.collapse_key:
                headers[PlatformType.collapse_key_key(platform_type)] = self.collapse_key

            if self.priority is not None:
                priority = PlatformPriority.platform_priority(platform_type, self.priority)
                headers[PlatformType.priority_key(platform_type)] = priority

            # Null out headers if they're empty
            headers = headers if headers else None

            if platform_type == PlatformType.APNS:
                # Create an empty `payload` as a workaround for an FCM bug
                # https://github.com/the-blue-alliance/the-blue-alliance/pull/2557#discussion_r310365295
                payload = messaging.APNSPayload(aps=messaging.Aps())
                return messaging.APNSConfig(headers=headers, payload=payload)
            elif platform_type == PlatformType.WEBPUSH:
                return messaging.WebpushConfig(headers=headers)
            else:
                raise TypeError("Unsupported PlatformPayload platform_type: {}".format(platform_type))
