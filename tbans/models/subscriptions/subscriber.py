class Subscriber:
    """
    Object that represents a token/error pair that comes back from a batch request.

    Attributes:
        token (string): Token for the subscriber.
        error (string, SubscriberError): Error returned from the batch request. May be None.
    """
    def __init__(self, token, result):
        """
        Args:
            token (string): Instance ID for the subscriber.
            result (dict): Dictionary result for the subscriber.
        """
        # Check that token looks right.
        if not isinstance(token, basestring) or not token:
            raise ValueError('Subscriber token must be a non-empty string.')
        self.token = token

        # Check that result looks right.
        if not isinstance(result, dict):
            raise TypeError('Subscriber result must be a dictionary.')

        self.error = result.get('error', None)
