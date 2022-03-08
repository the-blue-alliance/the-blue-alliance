from backend.tasks_io.tbans.models.notifications.requests.request import Request


WEBHOOK_VERSION = 1


class WebhookRequest(Request):
    """Represents a webhook notification payload.

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

        self.url = url
        self.secret = secret

    def __str__(self):
        return "WebhookRequest(notification={} url={})".format(
            str(self.notification), self.url
        )

    def send(self):
        """Attempt to send the notification."""
        # Build the request
        headers = {
            "Content-Type": 'application/json; charset="utf-8"',
            "X-TBA-Version": "{}".format(WEBHOOK_VERSION),
        }
        payload = self._json_string()
        # This checksum is insecure and has been deprecated in favor of an HMAC
        headers["X-TBA-Checksum"] = self._generate_webhook_checksum(payload)
        # Generate hmac
        headers["X-TBA-HMAC"] = self._generate_webhook_hmac(payload)

        import logging
        import urllib

        request = urllib.request.Request(self.url, payload, headers=headers)

        # TODO: Consider more useful way to surface error messages
        # https://github.com/the-blue-alliance/the-blue-alliance/issues/2576
        valid_url = True
        try:
            urllib.request.urlopen(request)
            self.defer_track_notification(1)
        except urllib.error.HTTPError as e:
            if e.code == 400:
                logging.warning("400, Bad request for URL: {}".format(self.url))
            elif e.code == 401:
                logging.warning(
                    "401, Webhook unauthorized for URL: {}".format(self.url)
                )
            elif e.code == 404:
                logging.warning("404, Invalid URL: {}".format(self.url))
                valid_url = False
            elif e.code == 500:
                logging.warning("500, Internal error on server sending message")
            else:
                logging.warning(
                    "Unexpected HTTPError: " + str(e.code) + " " + str(e.reason)
                )
        except urllib.error.URLError as e:
            valid_url = False
            logging.warning("URLError: " + str(e.reason))
        except Exception as ex:
            logging.warning(
                "Other Exception ({}): {}".format(ex.__class__.__name__, str(ex))
            )

        return valid_url

    def _json_string(self):
        """JSON string representation of an WebhookRequest object.

        JSON for WebhookRequest will look like...
        {
            "message_data": {...},
            "message_type": ...
        }

        Returns:
            string: JSON representation of the WebhookRequest.
        """
        from backend.common.consts.notification_type import (
            TYPE_NAMES as NOTIFICATION_TYPE_NAMES,
        )

        json_dict = {
            "message_type": NOTIFICATION_TYPE_NAMES[self.notification.__class__._type()]
        }

        if self.notification.webhook_message_data:
            json_dict["message_data"] = self.notification.webhook_message_data

        import json

        return json.dumps(json_dict, ensure_ascii=True)

    # This checksum is insecure and has been deprecated in favor of an HMAC
    def _generate_webhook_checksum(self, payload):
        import hashlib

        ch = hashlib.sha1()
        ch.update(self.secret.encode("utf-8"))
        ch.update(payload.encode("utf-8"))
        return ch.hexdigest()

    def _generate_webhook_hmac(self, payload):
        import hashlib
        import hmac

        return hmac.new(
            self.secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256
        ).hexdigest()
