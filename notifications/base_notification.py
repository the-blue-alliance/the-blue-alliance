import hashlib
import json
import logging
import urllib2

from google.appengine.ext import deferred

from controllers.gcm.gcm import GCMConnection
from consts.client_type import ClientType


class BaseNotification(object):

    """
    Class that acts as a basic notification.
    To send a notification, instantiate one and call this method
    """

    def send(self, keys):
        self.keys = keys  # dict like {ClientType : [ (key, secret) ] }
        for client_type in ClientType.names.keys():
            deferred.defer(self.render, client_type)

    """
    This method will create platform specific notifications and send them to the platform specified
    Clients should implement the referenced methods in order to build the notification for each platform
    """
    def render(self, client_type):
        if client_type == ClientType.OS_ANDROID and hasattr(self, "_render_android"):
            if ClientType.OS_ANDROID in self.keys and len(self.keys[ClientType.OS_ANDROID]) > 0:
                notification = self._render_android()
                self.send_gcm(notification)

        elif client_type == ClientType.OS_IOS and hasattr(self, "_render_ios"):
            notification = self._render_ios()
            self.send_ios(notification)

        elif client_type == ClientType.WEBHOOK and hasattr(self, "_render_webhook"):
            if ClientType.WEBHOOK in self.keys and len(self.keys[ClientType.WEBHOOK]) > 0:
                notification = self._render_webhook()
                self.send_webhook(notification)

    """
    Subclasses should override this method and return a dict containing the payload of the notification.
    The dict should have two entries: 'message_type' (should be one of NotificationType, string) and 'message_data'
    """
    def _build_dict(self):
        raise NotImplementedError("Subclasses must implement this method to build JSON data to send")

    def send_gcm(self, gcm_message):
        gcm_connection = GCMConnection()
        gcm_connection.notify_device(gcm_message)

    def send_ios(self, message):
        pass

    def send_webhook(self, message):
        payload = json.dumps(message, ensure_ascii=True)

        for client in self.keys[ClientType.WEBHOOK]:

            url = client[0]
            secret = client[1]

            ch = hashlib.sha1()
            ch.update(secret)
            ch.update(payload)
            checksum = ch.hexdigest()

            logging.info("Checksum: "+str(checksum))
            logging.info("URL: "+str(url))
            request = urllib2.Request(url, payload)
            request.add_header("X-Tba-Checksum", checksum)
            try:
                resp = urllib2.urlopen(request)

            except HTTPError, e:

                if e.code == 400:
                    logging.error('400, Invalid message: ' + repr(gcm_post_json_str))
                elif e.code == 401:
                    logging.error('401, Webhook unauthorized')
                elif e.code == 500:
                    logging.error('500, Internal error on server sending message')
                else:
                    logging.exception('Unexpected HTTPError: ' + str(e.code) + " " + e.msg + " " + e.read())

            except Exception, ex:
                logging.error("Other Exception: "+str(ex))
