class NotificationRequest(object):
    """ Base class used for requests to represent a notification payload.

    Attributes:
        notification (Notification): The Notification to send.
    """

    def __init__(self, notification):
        """
        Args:
            notification (Notification): The Notification to send.
        """
        from tbans.models.notifications.notification import Notification
        from tbans.utils.validation_utils import validate_is_type

        validate_is_type(Notification, notification=notification)
        self.notification = notification

    def json_string(self):
        """
        Returns:
            string: representation of message JSON.
        """
        raise NotImplementedError("NotificationRequest subclass must implement json_string")

    def send(self):
        """ NotificationRequests should understand how to send themselves to wherever they are going.

        Returns:
            NotificationResponse
        """
        raise NotImplementedError("NotificationRequest subclass must implement send")
