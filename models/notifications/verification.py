from models.notifications.notification import Notification


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
        self.url = url
        self.secret = secret
        self._generate_key()

    def _generate_key(self):
        import hashlib
        ch = hashlib.sha1()
        import time
        ch.update(str(time.time()))
        ch.update(self.url)
        ch.update(self.secret)
        self.verification_key = ch.hexdigest()

    @classmethod
    def _type(cls):
        from consts.notification_type import NotificationType
        return NotificationType.VERIFICATION

    # Only webhook message data is defined - because we'll only ever send verification to webhooks
    @property
    def webhook_message_data(self):
        return {'verification_key': self.verification_key}

    def _additional_logging_values(self):
        return [(self.verification_key, 'verification_key')]
