import logging

from google.appengine.ext import deferred

from controllers.gcm.gcm import GCMMessage
from consts.client_type import ClientType
from helpers.notification_sender import NotificationSender


class BaseNotification(object):

    _supported_clients = [ClientType.OS_ANDROID, ClientType.WEBHOOK]    # List of clients this notification type supports (these are default values)
                                                                        # Can be overridden by subclasses to only send to some types

    """
    Class that acts as a basic notification.
    To send a notification, instantiate one and call this method
    """

    def send(self, keys):
        self.keys = keys  # dict like {ClientType : [ key ] } ... The list for webhooks is a tuple of (key, secret)
        deferred.defer(self.render, self._supported_clients, _queue="push-notifications")

    """
    This method will create platform specific notifications and send them to the platform specified
    Clients should implement the referenced methods in order to build the notification for each platform
    """
    def render(self, client_types):
        for client_type in client_types:
            if client_type == ClientType.OS_ANDROID and ClientType.OS_ANDROID in self.keys:
                notification = self._render_android()
                if len(self.keys[ClientType.OS_ANDROID]) > 0:  # this is after _render because if it's an update fav/subscription notification, then
                    NotificationSender.send_gcm(notification)  # we remove the client id that sent the update so it doesn't get notified redundantly

            elif client_type == ClientType.OS_IOS and ClientType.OS_IOS in self.keys:
                notification = self._render_ios()
                NotificationSender.send_ios(notification)

            elif client_type == ClientType.WEBHOOK and ClientType.WEBHOOK in self.keys and len(self.keys[ClientType.WEBHOOK]) > 0:
                notification = self._render_webhook()
                NotificationSender.send_webhook(notification, self.keys[ClientType.WEBHOOK])

    """
    Subclasses should override this method and return a dict containing the payload of the notification.
    The dict should have two entries: 'message_type' (should be one of NotificationType, string) and 'message_data'
    """
    def _build_dict(self):
        raise NotImplementedError("Subclasses must implement this method to build JSON data to send")

    """
    The following methods are default render methods. Often, the way we construct the messages doesn't change, so we abstract it to here.
    However, if a notification type needs to do something special (e.g. specify a GCM collapse key), then subclasses can override them
    in order to provide that functionality.
    """
    def _render_android(self):
        gcm_keys = self.keys[ClientType.OS_ANDROID]
        data = self._build_dict()
        return GCMMessage(gcm_keys, data)

    def _render_ios(self):
        pass

    def _render_webhook(self):
        return self._build_dict()
