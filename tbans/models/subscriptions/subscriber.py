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
        from tbans.utils.validation_utils import validate_is_string, validate_is_type

        # Check that token looks right.
        validate_is_string(token=token)
        self.token = token

        # Check that result looks right.
        validate_is_type(dict, not_empty=False, result=result)
        self.error = result.get('error', None)

    def __str__(self):
        return 'Subscriber(token={}, error={})'.format(self.token, self.error)
