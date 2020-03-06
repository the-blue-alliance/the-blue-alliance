import logging
import random
import tba_config

from google.appengine.ext import deferred
from google.appengine.api import memcache

from consts.client_type import ClientType
from consts.notification_type import NotificationType
from helpers.notification_sender import NotificationSender
from sitevars.notifications_enable import NotificationsEnable


class BaseNotification(object):

    # List of clients this notification type supports (these are default values)
    # Can be overridden by subclasses to only send to some types
    _supported_clients = [ClientType.OS_ANDROID, ClientType.WEBHOOK]

    # Send analytics updates for this notification?
    # Can be overridden by subclasses if not
    _track_call = True

    # GCM Priority for this message, set to "High" for important pushes
    # Valid types are 'high' and 'normal'
    # https://developers.google.com/cloud-messaging/concept-options#setting-the-priority-of-a-message
    _priority = 'normal'

    # If set to (key, timeout_seconds), won't send multiple notifications
    _timeout = None

    """
    Class that acts as a basic notification.
    To send a notification, instantiate one and call this method
    """

    def send(self, keys, push_firebase=True, track_call=True):
        if self._timeout is not None:
            key, timeout = self._timeout
            if memcache.get(key):  # Using memcache is a hacky implementation, since it is not guaranteed.
                logging.info("Notification timeout for: {}".format(key))
                return  # Currently in timeout. Don't send.
            else:
                memcache.set(key, True, timeout)

        self.keys = keys  # dict like {ClientType : [ key ] } ... The list for webhooks is a tuple of (key, secret)
        deferred.defer(self.render, self._supported_clients, _target='backend-tasks', _queue='push-notifications', _url='/_ah/queue/deferred_notification_send')
        if self._track_call and track_call:
            num_keys = 0
            for v in keys.values():
                # Count the number of clients receiving the notification
                num_keys += len(v)
            if random.random() < tba_config.GA_RECORD_FRACTION:
                deferred.defer(self.track_notification, self._type, num_keys, _target='backend-tasks', _queue='api-track-call', _url='/_ah/queue/deferred_notification_track_send')

    """
    This method will create platform specific notifications and send them to the platform specified
    Clients should implement the referenced methods in order to build the notification for each platform
    """
    def render(self, client_types):
        if not isinstance(client_types, list):
            # Listify client types, if needed
            client_types = [client_types]

        if not self.check_enabled():
            # Don't send for NotificationTypes that aren't enabled
            return

        for client_type in client_types:
            if client_type is ClientType.OS_ANDROID and client_type in self.keys:
                client_render_method = self.render_method(client_type)
                notification = client_render_method()
                if len(self.keys[client_type]) > 0:  # this is after _render because if it's an update fav/subscription notification, then
                    NotificationSender.send_gcm(notification)  # we remove the client id that sent the update so it doesn't get notified redundantly

            elif client_type == ClientType.WEBHOOK and ClientType.WEBHOOK in self.keys and len(self.keys[ClientType.WEBHOOK]) > 0:
                notification = self._render_webhook()
                NotificationSender.send_webhook(notification, self.keys[ClientType.WEBHOOK])

    def check_enabled(self):
        return NotificationsEnable.notifications_enabled()

    """
    Subclasses should override this method and return a dict containing the payload of the notification.
    The dict should have two entries: 'notification_type' (should be one of NotificationType, string) and 'message_data'
    """
    def _build_dict(self):
        raise NotImplementedError("Subclasses must implement this method to build JSON data to send")

    @property
    def _type(self):
        raise NotImplementedError("Subclasses must implement this message to set its notification type")

    """
    The following methods are default render methods. Often, the way we construct the messages doesn't change, so we abstract it to here.
    However, if a notification type needs to do something special (e.g. specify a GCM collapse key), then subclasses can override them
    in order to provide that functionality.
    """
    def _render_android(self):
        return self._render_gcm(ClientType.OS_ANDROID)

    def _render_webhook(self):
        # Note: webhooks use `message_type` instead of the `notification_type`
        data = self._build_dict()
        message_type = data.pop('notification_type')
        data['message_type'] = message_type
        return data

    def _render_gcm(self, client_type):
        from controllers.gcm.gcm import GCMMessage
        gcm_keys = self.keys[client_type]
        data = self._build_dict()
        return GCMMessage(gcm_keys, data, priority=self._priority)

    def render_method(self, client_type):
        if client_type == ClientType.OS_ANDROID:
            return self._render_android
        elif client_type == ClientType.WEBHOOK:
            return self._render_webhook
        else:
            return self._render_gcm(client_type)

    # used for deferred analytics call
    def track_notification(self, notification_type_enum, num_keys):
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
