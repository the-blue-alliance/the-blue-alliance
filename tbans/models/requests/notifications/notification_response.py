class NotificationResponse(object):
    """ Base class, returned from a NotificationRequest's `send` method.

    Attributes:
        status_code (int): The stauts code from the HTTP response
        content (string): The content from the HTTP response - may be None
    """

    def __init__(self, status_code, content=None):
        """
        Args:
            status_code (int): The stauts code from the HTTP response
            content (string): The content from the HTTP response - may be None
        """
        from tbans.utils.validation_utils import validate_is_string, validate_is_type

        # Check that we have a status_code
        validate_is_type(int, not_empty=False, status_code=status_code)
        self.status_code = status_code

        # Check that content looks right
        if content:
            validate_is_string(content=content)
        self.content = content

    def __str__(self):
        return 'NotificationResponse(code={} content={})'.format(self.status_code, '"{}"'.format(self.content) if self.content else None)
