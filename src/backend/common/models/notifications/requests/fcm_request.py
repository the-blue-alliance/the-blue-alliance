import warnings
from typing import TYPE_CHECKING

from backend.common.models.mobile_client import MobileClient
from backend.common.models.notifications.notification import Notification
from backend.common.models.notifications.requests.request import Request

if TYPE_CHECKING:
    import firebase_admin

# firebase-admin's MulticastMessage caps tokens and fids at 500 combined
MAXIMUM_TOKENS = 500


class FCMRequest(Request):
    """Represents a notification payload and a delivery option to send to FCM.
    https://firebase.google.com/docs/reference/fcm/rest/v1/projects.messages
    Attributes:
        notification (Notification): The Notification to send.
        tokens (list, string): The legacy FCM registration tokens to send a message to.
        fids (list, string): The Firebase Installation IDs to send a message to.
    """

    def __init__(
        self,
        app: "firebase_admin.App",
        notification: Notification,
        tokens: list[str] | None = None,
        fids: list[str] | None = None,
    ) -> None:
        super(FCMRequest, self).__init__(notification=notification)

        self._app = app

        self.tokens: list[str] = tokens or []
        self.fids: list[str] = fids or []

        if not self.tokens and not self.fids:
            raise ValueError("FCMRequest must contain at least one token or fid")

        if len(self.tokens) + len(self.fids) > MAXIMUM_TOKENS:
            raise ValueError(
                f"FCMRequest must not contain more than {MAXIMUM_TOKENS} tokens/fids"
            )

    @classmethod
    def for_clients(
        cls,
        app: "firebase_admin.App",
        notification: Notification,
        clients: list[MobileClient],
    ) -> "FCMRequest":
        return cls(
            app,
            notification,
            tokens=[client.messaging_id for client in clients if not client.is_fid],
            fids=[client.messaging_id for client in clients if client.is_fid],
        )

    @property
    def messaging_ids(self) -> list[str]:
        """
        The order of `BatchResponse.responses` from `send`: firebase-admin expands a
        multicast into one message per token, then one per fid. This is not the order
        of the clients passed to `for_clients`.
        """
        return self.tokens + self.fids

    def __str__(self):
        return "FCMRequest(tokens={}, fids={}, notification={})".format(
            self.tokens, self.fids, str(self.notification)
        )

    def send(self):
        """Attempt to send the notification.
        Returns:
            messaging.BatchResponse - Batch response object for the messages sent.
        """
        from firebase_admin import messaging

        response = messaging.send_each_for_multicast(self._fcm_message(), app=self._app)
        if response.success_count > 0:
            try:
                self.defer_track_notification(response.success_count)
            except Exception:
                pass
        return response

    def _fcm_message(self):
        from firebase_admin import messaging

        platform_config = self.notification.platform_config

        # `platform_config and ...` short circuits if platform_config is None
        android_config = (
            self.notification.android_config
            if self.notification.android_config
            else platform_config and platform_config.android_config()
        )
        apns_config = (
            self.notification.apns_config
            if self.notification.apns_config
            else platform_config and platform_config.apns_config()
        )
        webpush_config = (
            self.notification.webpush_config
            if self.notification.webpush_config
            else platform_config and platform_config.webpush_config()
        )

        # Additional APNS-specific configuration - make sure we have some payload
        if not apns_config:
            apns_config = messaging.APNSConfig()
        if not apns_config.payload:
            apns_config.payload = messaging.APNSPayload(aps=messaging.Aps())

        if self.notification.fcm_notification:
            # Set sound
            apns_config.payload.aps.sound = "default"
        else:
            # Set content_available
            apns_config.payload.aps.content_available = True

        # Setup data payload - base case for None data payloads
        data_payload = (
            self.notification.data_payload if self.notification.data_payload else {}
        )
        # Remove `None` from data payload, since FCM won't accept them
        data_payload = {k: v for k, v in data_payload.items() if v is not None}
        from backend.common.consts.notification_type import (
            TYPE_NAMES as NOTIFICATION_TYPE_NAMES,
        )

        # Add `notification_type` to data payload
        data_payload["notification_type"] = NOTIFICATION_TYPE_NAMES[
            self.notification.__class__._type()
        ]

        with warnings.catch_warnings():
            # firebase-admin 7.5.0 deprecated `tokens` in favor of `fids`, and pytest
            # runs with `filterwarnings = error`. Ignore only that warning, so any other
            # deprecation still surfaces, including in a request that mixes the two.
            warnings.filterwarnings(
                "ignore",
                message=r"MulticastMessage\.tokens is deprecated",
                category=DeprecationWarning,
            )
            return messaging.MulticastMessage(
                tokens=self.tokens or None,
                fids=self.fids or None,
                data=data_payload,
                notification=self.notification.fcm_notification,
                android=android_config,
                webpush=webpush_config,
                apns=apns_config,
            )
