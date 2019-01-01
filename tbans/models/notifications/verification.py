import hashlib
import time

from consts.notification_type import NotificationType
from tbans.models.notifications.notification import Notification


class VerificationNotification(Notification):
    """ Verification notification - used for webhooks to ensure the proper people are in control

    Attributes:
        url (string): The URL to send the notification payload to.
        secret (string): The secret to calculate the payload checksum with.
        verification_key (string): SHA1 of url + secret
    """

    def __init__(self, url, secret):
        """
        Args:
            url (string): The URL to send the notification payload to.
            secret (string): The secret to calculate the payload checksum with.
        """
        # Check url, secret
        for (value, name) in [(url, 'url'), (secret, 'secret')]:
            # Make sure our value exists
            if value is None:
                raise ValueError('VerificationNotification requires a {}'.format(name))
            # Check that our value looks right
            if not isinstance(value, basestring):
                raise TypeError('VerificationNotification {} must be an string'.format(name))

        self.url = url
        self.secret = secret
        self._generate_key()

    def _generate_key(self):
        ch = hashlib.sha1()
        ch.update(str(time.time()))
        ch.update(self.url)
        ch.update(self.secret)
        self.verification_key = ch.hexdigest()

    @staticmethod
    def _type():
        return NotificationType.VERIFICATION

    # Only webhook payload is defined - because we'll only ever send verification to webhooks
    @property
    def webhook_payload(self):
        return {'verification_key': self.verification_key}

    def _additional_logging_values(self):
        return [(self.verification_key, 'verification_key')]
