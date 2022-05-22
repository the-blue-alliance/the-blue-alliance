from backend.common.google_analytics import GoogleAnalytics
from backend.tasks_io.models.notifications.notification import Notification


class Request(object):
    """Base class used for requests to represent a notification payload.

    Attributes:
        notification (Notification): The Notification to send.
    """

    def __init__(self, notification: Notification) -> None:
        """
        Args:
            notification (Notification): The Notification to send.
        """
        self.notification = notification

    def send(self) -> None:  # TODO: Return type here appears to be non-standard
        """NotificationRequests should understand how to send themselves to wherever they are going.

        Returns:
            NotificationResponse
        """
        raise NotImplementedError("NotificationRequest subclass must implement send")

    def defer_track_notification(self, num_keys: int) -> None:
        from google.appengine.ext import deferred

        from backend.common.consts.notification_type import (
            TYPE_NAMES as NOTIFICATION_TYPE_NAMES,
        )

        deferred.defer(
            GoogleAnalytics.track_event,
            "tba-notification-tracking",
            "notification",
            NOTIFICATION_TYPE_NAMES[type(self.notification)._type()],
            event_value=num_keys,
            _queue="api-track-call",
            _url="/_ah/queue/deferred_notification_track_send",
        )
