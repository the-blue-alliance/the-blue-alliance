class PlatformPayloadPriority:
    """
    Constants regarding the priority of a push notification
    """

    NORMAL = 0
    HIGH = 1

    types = [NORMAL, HIGH]  # All supported platform payload priorities

    # https://firebase.google.com/docs/reference/fcm/rest/v1/projects.messages#androidmessagepriority
    android = {
        NORMAL: 'NORMAL',
        HIGH: 'HIGH',
    }

    # https://developer.apple.com/library/archive/documentation/NetworkingInternet/Conceptual/RemoteNotificationsPG/CommunicatingwithAPNs.html#//apple_ref/doc/uid/TP40008194-CH11-SW1
    apns = {
        NORMAL: '5',
        HIGH: '10',
    }
    # Note: Do not use HIGH for iOS notifications when notifications only contain content-available

    # https://developers.google.com/web/fundamentals/push-notifications/web-push-protocol#urgency
    web = {
        NORMAL: 'normal',
        HIGH: 'high',
    }
