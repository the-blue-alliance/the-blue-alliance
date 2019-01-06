
class PlatformPayloadType(object):
    """
    Constants for the type of platform payloads
    https://firebase.google.com/docs/reference/fcm/rest/v1/projects.messages
    """

    ANDROID = 0
    APNS = 1
    WEBPUSH = 2

    types = [ANDROID, APNS, WEBPUSH]  # All supported platform payload types

    key_names = {
        ANDROID: 'android',
        APNS: 'apns',
        WEBPUSH: 'webpush'
    }
