
class ClientType:

    # Operating System types for MobileClient.client_type
    OS_ANDROID = 0
    OS_IOS = 1
    WEBHOOK = 2

    names = {
        OS_ANDROID: 'android',
        OS_IOS: 'ios',
        WEBHOOK: 'webhook'
    }

    enums = {
        'android': OS_ANDROID,
        'ios': OS_IOS,
        'webhook': WEBHOOK
    }
