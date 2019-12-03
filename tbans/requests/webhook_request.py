from tbans.requests.request import Request


WEBHOOK_VERSION = 1


class WebhookRequest(Request):
    """ Represents a webhook notification payload.

    Attributes:
        notification (Notification): The Notification to send.
        url (string): The URL to send the notification payload to.
        secret (string): The secret to calculate the payload checksum with.
    """

    def __init__(self, notification, url, secret):
        """
        Args:
            notification (Notification): The Notification to send.
            url (string): The URL to send the notification payload to.
            secret (string): The secret to calculate the payload checksum with.
        """
        super(WebhookRequest, self).__init__(notification)

        from tbans.utils.validation_utils import validate_is_string, validate_is_type

        # Check that we have a url
        validate_is_string(url=url)
        self.url = url

        # Check that we have a secret
        validate_is_string(secret=secret)
        self.secret = secret

    def __str__(self):
        return 'WebhookRequest(notification={} url={})'.format(str(self.notification), self.url)

    def send(self):
        """ Attempt to send the notification."""
        # Build the request
        headers = {
            'Content-Type': 'application/json',
            'X-TBA-Version': '{}'.format(WEBHOOK_VERSION)
        }
        message_json = self._json_string()
        # This checksum is insecure and has been deprecated in favor of an HMAC
        headers['X-TBA-Checksum'] = self._generate_webhook_checksum(message_json)
        # Generate hmac
        headers['X-TBA-HMAC'] = self._generate_webhook_hmac(message_json)

        from google.appengine.api import urlfetch
        return urlfetch.fetch(url=self.url, payload=message_json, method=urlfetch.POST, headers=headers)

    def _json_string(self):
        """ JSON string representation of an WebhookRequest object.

        JSON for WebhookRequest will look like...
        {
            'message_data': {...},
            'message_type': ...
        }

        Returns:
            string: JSON representation of the WebhookRequest.
        """
        from consts.notification_type import NotificationType
        json_dict = {
            'message_type': NotificationType.type_names[self.notification.__class__._type()]
        }

        if self.notification.webhook_message_data:
            json_dict['message_data'] = self.notification.webhook_message_data

        import json
        return json.dumps(json_dict, ensure_ascii=True)

    # This checksum is insecure and has been deprecated in favor of an HMAC
    def _generate_webhook_checksum(self, payload):
        import hashlib
        ch = hashlib.sha1()
        ch.update(self.secret)
        ch.update(payload)
        return ch.hexdigest()

    def _generate_webhook_hmac(self, payload):
        import hashlib
        import hmac

        # Always cast via `str()` to ensure we handle unicode properly in Python 2
        return hmac.new(str(self.secret), str(payload), hashlib.sha256).hexdigest()
