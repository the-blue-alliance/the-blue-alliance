import hashlib
import json

from google.appengine.api import urlfetch

from consts.notification_type import NotificationType
from tbans.models.messages.message import Message
from tbans.models.messages.message_response import MessageResponse


WEBHOOK_VERSION = 1


class WebhookMessage(Message):
    """ Represents a webhook notification payload

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
        super(WebhookMessage, self).__init__(notification)

        # Check that we have a url
        if url is None:
            raise ValueError('WebhookMessage requires a url')
        # Check that our url looks right
        if not isinstance(url, basestring):
            raise TypeError('WebhookMessage url must be a string')
        self.url = url

        # Check that we have a secret
        if secret is None:
            raise ValueError('WebhookMessage requires a secret')
        # Check that our url looks right
        if not isinstance(secret, basestring):
            raise TypeError('WebhookMessage secret must be a string')
        self.secret = secret

    def __str__(self):
        return 'WebhookMessage(notification={})'.format(str(self.notification))

    def json_string(self):
        """ JSON string representation of an WebhookMessage object

        JSON for WebhookMessage will look like...
        {
            'message_data': {...},
            'message_type': ...
        }

        Returns:
            string: JSON representation of the FCMMessage
        """

        json_dict = {
            'message_type': NotificationType.type_names[type(self.notification)._type()]
        }

        if self.notification.webhook_payload:
            json_dict['message_data'] = self.notification.webhook_payload

        return json.dumps(json_dict, ensure_ascii=True)

    def send(self):
        """ Attempt to send the WebhookMessage

        Returns:
            MessageResponse, content/status_code
        """
        # Build the request
        headers = {
            'Content-Type': 'application/json',
            'X-TBA-Version': '{}'.format(WEBHOOK_VERSION)
        }
        message_json = self.json_string()
        # Generate checksum
        headers['X-TBA-Checksum'] = self._generate_webhook_checksum(message_json)

        try:
            response = urlfetch.fetch(
                url=self.url,
                payload=message_json,
                method='POST',
                headers=headers
            )
            return MessageResponse(response.status_code, response.content)
        except Exception, e:
            # https://cloud.google.com/appengine/docs/standard/python/refdocs/google.appengine.api.urlfetch_errors
            return MessageResponse(500, str(e))

    def _generate_webhook_checksum(self, payload):
        ch = hashlib.sha1()
        ch.update(self.secret)
        ch.update(payload)
        return ch.hexdigest()
