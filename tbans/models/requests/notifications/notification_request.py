from tbans.models.notifications.notification import Notification


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
        class_name = self.__class__.__name__
        if notification is None:
            raise ValueError('{} notification cannot be None'.format(class_name))
        if not isinstance(notification, Notification):
            raise TypeError('{} notification must be a Notification subclass'.format(class_name))
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
