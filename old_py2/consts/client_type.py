class ClientType:

    # Operating System types for MobileClient.client_type
    OS_ANDROID = 0
    OS_IOS = 1
    WEBHOOK = 2
    WEB = 3

    # List of ClientType that are able to subscribe to push notifications via TBANS
    # TODO: Move Android from old notification code to new notification code
    FCM_CLIENTS = [OS_IOS, WEB]

    names = {
        OS_ANDROID: 'android',
        OS_IOS: 'ios',
        WEBHOOK: 'webhook',
        WEB: 'web'
    }

    enums = {
        'android': OS_ANDROID,
        'ios': OS_IOS,
        'webhook': WEBHOOK,
        'web': WEB
    }
