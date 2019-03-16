class IIDError:
    INTERNAL_ERROR = 'internal-error'
    UNKNOWN_ERROR = 'unknown-error'
    INVALID_ARGUMENT = 'invalid-argument'
    AUTHENTICATION_ERROR = 'authentication-error'
    SERVER_UNAVAILABLE = 'server-unavailable'

    ERROR_CODES = {
        400: INVALID_ARGUMENT,
        401: AUTHENTICATION_ERROR,
        403: AUTHENTICATION_ERROR,
        500: INTERNAL_ERROR,
        503: SERVER_UNAVAILABLE
    }
