from typing import Any, Dict, List, Optional, Tuple

from backend.common.consts.notification_type import NotificationType
from backend.common.models.fcm.platform_config import PlatformConfig
from backend.common.models.mobile_client import MobileClient


class Notification(object):
    """
    Base notification classs - represents message, data, and platform config payloads for notifications.
    """

    def __str__(self) -> str:
        values = [
            value
            for value in [
                (self.data_payload, "data_payload"),
                (
                    self.fcm_notification
                    and '"{}"'.format(self.fcm_notification.title),
                    "fcm_notification.title",
                ),
                (
                    self.fcm_notification and '"{}"'.format(self.fcm_notification.body),
                    "fcm_notification.body",
                ),
                (self.platform_config, "platform_config"),
                (self.android_config, "android_config"),
                (self.apns_config and self.apns_config.headers, "apns_config"),
                (self.webpush_config and self.webpush_config.headers, "webpush_config"),
                (self.webhook_message_data, "webhook_message_data"),
            ]
            + self._additional_logging_values()
            if value[0] is not None
        ]
        value_strings = [
            "{}={}".format(str(value[1]), str(value[0])) for value in values
        ]
        value_string = " ".join(value_strings)
        return f"{self.__class__.__name__}({value_string})"

    @classmethod
    def _type(cls) -> NotificationType:
        """Corresponding NotificationType for this notification

        Returns:
            NotificationType constant
        """
        raise NotImplementedError("Notification subclass must implement type")

    def should_send_to_client(self, client: MobileClient) -> bool:
        """
        Provide a way to filter out a given notification from being sent to certain
        recipients

        Returns:
            boolean indicating if we should attempt to send the notification or not
        """
        return True

    @property
    def fcm_notification(self) -> Optional[Any]:
        """FCM Notification object to use for FCM.

        Returns:
            firebase_admin.messaging.Notification: None if no notification.
        """
        return None

    @property
    def data_payload(self) -> Optional[Dict[str, str]]:
        """Arbitrary key/value payload.

        Returns:
            dictionary, or None if no data payload.
        """
        return None

    @property
    def platform_config(self) -> Optional[PlatformConfig]:
        """Default config to use for all platforms.

        Note:
            If you implement android_config, apns_config, or webpush_config,
            those values will be used for their specific platforms instead of this one.

        Returns:
            backend.common.models.fcm.platform_config.PlatformConfig: None if no platform config is necessary.
        """
        return None

    @property
    def android_config(self) -> Optional[Any]:
        """Android specific options for messages sent through FCM connection server.

        Returns:
            firebase_admin.messaging.AndroidConfig: None if no Android-specific config is necessary.
        """
        return None

    @property
    def apns_config(self) -> Optional[Any]:
        """Apple Push Notification Service specific options for messages sent through FCM connection server.

        Returns:
            firebase_admin.messaging.ApnsConfig: None if no APNS-specific config is necessary.
        """
        return None

    @property
    def webpush_config(self) -> Optional[Any]:
        """Webpush protocol options for messages sent through FCM connection server.

        Returns:
            firebase_admin.messaging.WebpushConfig: None if no webpush-specific config is necessary.
        """
        return None

    @property
    def webhook_message_data(self) -> Optional[Dict[str, Any]]:
        """`message_data` dictionary for a webhook request.

        Note:
            By default, will fall back to using the data_payload.

        Returns:
            dictionary: None if no webhook data payload.
        """
        return self.data_payload

    def _additional_logging_values(self) -> List[Tuple[str, str]]:
        """Return a list of value (or None)/name tuples to be adding to str for logging"""
        return []
