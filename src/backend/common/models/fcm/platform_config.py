from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from pyre_extensions import none_throws

from backend.common.consts.fcm.platform_priority import PlatformPriority
from backend.common.consts.fcm.platform_type import PlatformType

if TYPE_CHECKING:
    from firebase_admin.messaging import AndroidConfig, APNSConfig, WebpushConfig


class PlatformConfig:
    """
    Represents platform-specific push notification configuration options.

    https://firebase.google.com/docs/reference/fcm/rest/v1/projects.messages

    Args:
        collapse_key (string): Collapse key for push notification - may be None.
        priority (PlatformPriority): Priority for push notification - may be None.
    """

    # TODO: Add ttl
    def __init__(
        self,
        collapse_key: Optional[str] = None,
        priority: Optional[PlatformPriority] = None,
    ) -> None:
        """
        Args:
            collapse_key (string): Collapse key for push notification - may be None.
            priority (PlatformPriority): Priority for push notification - may be None.
        """
        self.collapse_key = collapse_key

        # Check that our priority looks right
        if priority:
            PlatformPriority.validate(priority)
        self.priority = priority

    def __str__(self) -> str:
        return 'PlatformConfig(collapse_key="{}" priority={})'.format(
            self.collapse_key, self.priority
        )

    def android_config(self) -> AndroidConfig:
        """Return the AndroidConfig for this platform payload."""
        from firebase_admin import messaging

        priority = None
        if self.priority is not None:
            priority = PlatformPriority.platform_priority(
                PlatformType.ANDROID, none_throws(self.priority)
            )

        return messaging.AndroidConfig(
            collapse_key=self.collapse_key, priority=priority
        )

    def apns_config(self) -> APNSConfig:
        """Return the APNSConfig for this platform payload."""
        from firebase_admin import messaging

        return messaging.APNSConfig(
            headers=self._headers(PlatformType.APNS),
            # Create an empty `payload` as a workaround for an FCM bug
            # https://github.com/the-blue-alliance/the-blue-alliance/pull/2557#discussion_r310365295
            payload=messaging.APNSPayload(aps=messaging.Aps()),
        )

    def webpush_config(self) -> WebpushConfig:
        """Return the WebpushConfig for this platform payload."""
        from firebase_admin import messaging

        return messaging.WebpushConfig(headers=self._headers(PlatformType.WEBPUSH))

    def _headers(self, platform_type: PlatformType) -> Optional[dict[str, str]]:
        """Collapse key and priority as headers, or None if neither is set."""
        headers = {}

        if self.collapse_key:
            headers[PlatformType.collapse_key_key(platform_type)] = self.collapse_key

        if self.priority is not None:
            headers[PlatformType.priority_key(platform_type)] = (
                PlatformPriority.platform_priority(
                    platform_type, none_throws(self.priority)
                )
            )

        return headers or None
