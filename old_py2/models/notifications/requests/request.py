import logging


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
        self.notification = notification

    def send(self):
        """ NotificationRequests should understand how to send themselves to wherever they are going.

        Returns:
            NotificationResponse
        """
        raise NotImplementedError("NotificationRequest subclass must implement send")

    def defer_track_notification(self, num_keys):
        from google.appengine.ext import deferred
        deferred.defer(_track_notification, type(self.notification)._type(), num_keys, _target='backend-tasks', _queue='api-track-call', _url='/_ah/queue/deferred_notification_track_send')


def _track_notification(notification_type_enum, num_keys):
    """
    For more information about GAnalytics Protocol Parameters, visit
    https://developers.google.com/analytics/devguides/collection/protocol/v1/parameters
    """
    from sitevars.google_analytics_id import GoogleAnalyticsID
    google_analytics_id = GoogleAnalyticsID.google_analytics_id()
    if not google_analytics_id:
        logging.warning("Missing sitevar: google_analytics.id. Can't track API usage.")
    else:
        import uuid
        cid = uuid.uuid3(uuid.NAMESPACE_X500, str('tba-notification-tracking'))

        from consts.notification_type import NotificationType
        from urllib import urlencode
        params = urlencode({
            'v': 1,
            'tid': google_analytics_id,
            'cid': cid,
            't': 'event',
            'ec': 'notification',
            'ea': NotificationType.type_names[notification_type_enum],
            'ev': num_keys,
            'ni': 1,
            'sc': 'end',  # forces tracking session to end
        })

        from google.appengine.api import urlfetch
        analytics_url = 'http://www.google-analytics.com/collect?%s' % params
        urlfetch.fetch(
            url=analytics_url,
            method=urlfetch.GET,
            deadline=10,
        )
