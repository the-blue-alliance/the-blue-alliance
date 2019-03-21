class NotificationPayload(object):
    """
    Basic notification template to use across all platforms.

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
        from tbans.utils.validation_utils import validate_is_string

        # Check that we have a title
        validate_is_string(title=title)
        self.title = title

        # Check that we have a body
        validate_is_string(body=body)
        self.body = body

    def __str__(self):
        return 'NotificationPayload(title="{}" body="{}")'.format(self.title, self.body)

    @property
    def payload_dict(self):
        return {
            'title': self.title,
            'body': self.body,
        }
