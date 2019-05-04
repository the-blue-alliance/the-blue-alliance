class Request(object):
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

    def send(self):
        """ NotificationRequests should understand how to send themselves to wherever they are going.

        Returns:
            NotificationResponse
        """
        raise NotImplementedError("NotificationRequest subclass must implement send")

    # TODO: Add Google Analytics logging
    # https://github.com/the-blue-alliance/the-blue-alliance/blob/master/notifications/base_notification.py#L141
