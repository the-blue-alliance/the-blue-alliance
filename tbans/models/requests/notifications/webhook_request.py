from tbans.models.requests.notifications.notification_request import NotificationRequest


WEBHOOK_VERSION = 1


class WebhookRequest(NotificationRequest):
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
        validate_is_type(basestring, not_empty=False, secret=secret)
        self.secret = secret

    def __str__(self):
        return 'WebhookRequest(notification={})'.format(str(self.notification))

    def json_string(self):
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
            'message_type': NotificationType.type_names[type(self.notification)._type()]
        }

        if self.notification.webhook_payload:
            json_dict['message_data'] = self.notification.webhook_payload

        import json
        return json.dumps(json_dict, ensure_ascii=True)

    def send(self):
        """ Attempt to send the WebhookRequest.

        Returns:
            NotificationResponse: content/status_code
        """
        # Build the request
        headers = {
            'Content-Type': 'application/json',
            'X-TBA-Version': '{}'.format(WEBHOOK_VERSION)
        }
        message_json = self.json_string()
        # Generate checksum
        headers['X-TBA-Checksum'] = self._generate_webhook_checksum(message_json)

        from google.appengine.api import urlfetch
        rpc = urlfetch.create_rpc()

        from tbans.models.requests.notifications.notification_response import NotificationResponse
        try:
            urlfetch.make_fetch_call(rpc, self.url, payload=message_json, method=urlfetch.POST, headers=headers)
            return NotificationResponse(200, None)
        except Exception, e:
            # https://cloud.google.com/appengine/docs/standard/python/refdocs/google.appengine.api.urlfetch
            return NotificationResponse(500, str(e))

    def _generate_webhook_checksum(self, payload):
        import hashlib
        ch = hashlib.sha1()
        ch.update(self.secret)
        ch.update(payload)
        return ch.hexdigest()
