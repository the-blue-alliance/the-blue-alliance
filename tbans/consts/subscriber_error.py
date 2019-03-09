class SubscriberError:
    NOT_FOUND = 'NOT_FOUND'
    INVALID_ARGUMENT = 'INVALID_ARGUMENT'
    INTERNAL = 'INTERNAL'
    TOO_MANY_TOPICS = 'TOO_MANY_TOPICS'

    ERRORS_MESSAGE = {
        NOT_FOUND: 'The registration token has been deleted or the app has been uninstalled.',
        INVALID_ARGUMENT: 'The registration token provided is not valid for the Sender ID.',
        INTERNAL: 'The backend server failed for unknown reasons. Retry the request.',
        TOO_MANY_TOPICS: 'Excessive number of topics per app instance.'
    }
