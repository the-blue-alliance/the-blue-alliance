
class MessageResponse(object):
    """ Base class, returned from a Message's `send` method

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
        # Check that we have a status_code
        if status_code is None:
            raise ValueError('MessageResponse requires a status_code')
        # Check that our status_code looks right
        if not isinstance(status_code, int):
            raise TypeError('MessageResponse status_code must be an int')
        self.status_code = status_code

        # Check that content looks right
        if content:
            if not isinstance(content, basestring):
                raise TypeError('MessageResponse content must be a string')
        self.content = content

    def __str__(self):
        return 'MessageResponse(code={} content={})'.format(self.status_code, '"{}"'.format(self.content) if self.content else None)
