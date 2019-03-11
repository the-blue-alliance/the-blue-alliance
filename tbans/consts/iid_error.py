class IIDError:
    INTERNAL_ERROR = 'internal-error'
    UNKNOWN_ERROR = 'unknown-error'
    ERROR_CODES = {
        400: 'invalid-argument',
        401: 'authentication-error',
        403: 'authentication-error',
        500: INTERNAL_ERROR,
        503: 'server-unavailable'
    }
