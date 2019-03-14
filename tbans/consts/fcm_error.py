class FCMError:
    INTERNAL_ERROR = 'internal-error'
    UNKNOWN_ERROR = 'unknown-error'
    ERROR_CODES = {
        # FCM v1 canonical error codes
        'NOT_FOUND': 'registration-token-not-registered',
        'PERMISSION_DENIED': 'mismatched-credential',
        'RESOURCE_EXHAUSTED': 'message-rate-exceeded',
        'UNAUTHENTICATED': 'invalid-apns-credentials',

        # FCM v1 new error codes
        'APNS_AUTH_ERROR': 'invalid-apns-credentials',
        'INTERNAL': INTERNAL_ERROR,
        'INVALID_ARGUMENT': 'invalid-argument',
        'QUOTA_EXCEEDED': 'message-rate-exceeded',
        'SENDER_ID_MISMATCH': 'mismatched-credential',
        'UNAVAILABLE': 'server-unavailable',
        'UNREGISTERED': 'registration-token-not-registered',
    }
