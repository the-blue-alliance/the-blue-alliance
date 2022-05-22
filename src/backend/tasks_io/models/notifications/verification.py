from typing import Any, Dict, List, Optional, Tuple

from backend.common.consts.notification_type import NotificationType
from backend.tasks_io.models.notifications import Notification


class VerificationNotification(Notification):
    """Verification notification - used for webhooks to ensure the proper people are in control

    Attributes:
        url (string): The URL to send the notification payload to.
        secret (string): The secret to calculate the payload checksum with.
        verification_key (string): SHA1 of url + secret
    """

    def __init__(self, url: str, secret: str) -> None:
        """
        Args:
            url (string): The URL to send the notification payload to.
            secret (string): The secret to calculate the payload checksum with.
        """
        self.url = url
        self.secret = secret
        self._generate_key()

    def _generate_key(self) -> None:
        import hashlib

        ch = hashlib.sha1()
        import time

        ch.update(str(time.time()).encode("utf-8"))
        ch.update(self.url.encode("utf-8"))
        ch.update(self.secret.encode("utf-8"))
        self.verification_key = ch.hexdigest()

    @classmethod
    def _type(cls) -> NotificationType:
        return NotificationType.VERIFICATION

    # Only webhook message data is defined - because we'll only ever send verification to webhooks
    @property
    def webhook_message_data(self) -> Optional[Dict[str, Any]]:
        return {"verification_key": self.verification_key}

    def _additional_logging_values(self) -> List[Tuple[str, str]]:
        return [(self.verification_key, "verification_key")]
