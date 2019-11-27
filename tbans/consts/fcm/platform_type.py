class PlatformType:
    """
    Constants for the type of FCM platforms.
    https://firebase.google.com/docs/reference/fcm/rest/v1/projects.messages
    """

    ANDROID = 0
    APNS = 1
    WEBPUSH = 2

    _types = [ANDROID, APNS, WEBPUSH]  # All supported platform payload types

    _priority_keys = {
        ANDROID: 'priority',
        APNS: 'apns-priority',
        WEBPUSH: 'Urgency'
    }

    _collapse_key_keys = {
        ANDROID: 'collapse_key',
        APNS: 'apns-collapse-id',
        WEBPUSH: 'Topic'
    }

    @classmethod
    def validate(cls, platform_type):
        """ Validate that the platform_type is supported.

        Raises:
            ValueError: If platform_type is an unsupported platform type.
        """
        if platform_type not in cls._types:
            raise ValueError("Unsupported platform_type: {}".format(platform_type))

    @classmethod
    def collapse_key_key(cls, platform_type):
        # Validate that platform_type is supported
        PlatformType.validate(platform_type)
        return cls._collapse_key_keys[platform_type]

    @classmethod
    def priority_key(cls, platform_type):
        # Validate that platform_type is supported
        PlatformType.validate(platform_type)
        return cls._priority_keys[platform_type]
