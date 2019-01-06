
class NotificationPayload(object):

    """
    Basic notification template to use across all platforms

    https://firebase.google.com/docs/reference/fcm/rest/v1/projects.messages#Notification

    Attributes:
        title (string): Title for the notification.
        body (string): Body message for the notification.
    """

    def __init__(self, title, body):
        """
        Args:
            title (string): Title for the notification.
            body (string): Body message for the notification.
        """
        # Check that we have a title
        if title is None:
            raise ValueError('NotificationPayload requires a title')
        # Check that our title looks right
        if not isinstance(title, basestring):
            raise TypeError('NotificationPayload title must be a string')
        self.title = title

        # Check that we have a body
        if body is None:
            raise ValueError('NotificationPayload requires a body')
        # Check that our body looks right
        if not isinstance(body, basestring):
            raise TypeError('NotificationPayload body must be a string')
        self.body = body

    def __str__(self):
        return 'NotificationPayload(title="{}" body="{}")'.format(self.title, self.body)

    @property
    def payload_dict(self):
        return {
            'title': self.title,
            'body': self.body,
        }
