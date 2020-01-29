class PlatformPriority:
    """
    Constants regarding the priority of a push notification.
    """

    NORMAL = 0
    HIGH = 1

    _types = [NORMAL, HIGH]  # All supported platform payload priorities

    # https://firebase.google.com/docs/reference/fcm/rest/v1/projects.messages#androidmessagepriority
    _android = {
        NORMAL: 'normal',
        HIGH: 'high',
    }

    # https://developer.apple.com/library/archive/documentation/NetworkingInternet/Conceptual/RemoteNotificationsPG/CommunicatingwithAPNs.html#//apple_ref/doc/uid/TP40008194-CH11-SW1
    _apns = {
        NORMAL: '5',
        HIGH: '10',
    }
    # Note: Do not use HIGH for iOS notifications when notifications only contain content-available

    # https://developers.google.com/web/fundamentals/push-notifications/web-push-protocol#urgency
    _web = {
        NORMAL: 'normal',
        HIGH: 'high',
    }

    @classmethod
    def validate(cls, platform_priority):
        """ Validate that the platform_priority is supported.

        Raises:
            ValueError: If platform_priority is an unsupported platform priority.
        """
        if platform_priority not in cls._types:
            raise ValueError("Unsupported platform_priority: {}".format(platform_priority))

    @classmethod
    def platform_priority(cls, platform_type, platform_priority):
        from consts.fcm.platform_type import PlatformType
        # Validate that platform_type is supported
        PlatformType.validate(platform_type)
        # Validate that platform_priority is supported
        PlatformPriority.validate(platform_priority)

        if platform_type == PlatformType.ANDROID:
            return cls._android[platform_priority]
        elif platform_type == PlatformType.APNS:
            return cls._apns[platform_priority]
        elif platform_type == PlatformType.WEBPUSH:
            return cls._web[platform_priority]
