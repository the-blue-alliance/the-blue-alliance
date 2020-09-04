from __future__ import annotations

import enum
from typing import Dict

from backend.tasks_io.tbans.consts.fcm.platform_type import PlatformType


@enum.unique
class PlatformPriority(enum.IntEnum):
    """
    Constants regarding the priority of a push notification.
    """

    NORMAL = 0
    HIGH = 1

    @staticmethod
    def validate(platform_priority: PlatformPriority) -> None:
        """Validate that the platform_priority is supported.

        Raises:
            ValueError: If platform_priority is an unsupported platform priority.
        """
        if platform_priority not in list(PlatformPriority):
            raise ValueError(
                "Unsupported platform_priority: {}".format(platform_priority)
            )

    @staticmethod
    def platform_priority(
        platform_type: PlatformType, platform_priority: PlatformPriority
    ) -> str:
        from backend.tasks_io.tbans.consts.fcm.platform_type import PlatformType

        # Validate that platform_type is supported
        PlatformType.validate(platform_type)
        # Validate that platform_priority is supported
        PlatformPriority.validate(platform_priority)

        # https://firebase.google.com/docs/reference/fcm/rest/v1/projects.messages#androidmessagepriority
        ANDROID: Dict[PlatformPriority, str] = {
            PlatformPriority.NORMAL: "normal",
            PlatformPriority.HIGH: "high",
        }

        # https://developer.apple.com/library/archive/documentation/NetworkingInternet/Conceptual/RemoteNotificationsPG/CommunicatingwithAPNs.html#//apple_ref/doc/uid/TP40008194-CH11-SW1
        APNS: Dict[PlatformPriority, str] = {
            PlatformPriority.NORMAL: "5",
            PlatformPriority.HIGH: "10",
        }
        # Note: Do not use HIGH for iOS notifications when notifications only contain content-available

        # https://developers.google.com/web/fundamentals/push-notifications/web-push-protocol#urgency
        WEB: Dict[PlatformPriority, str] = {
            PlatformPriority.NORMAL: "normal",
            PlatformPriority.HIGH: "high",
        }

        if platform_type == PlatformType.ANDROID:
            return ANDROID[platform_priority]
        elif platform_type == PlatformType.APNS:
            return APNS[platform_priority]
        return WEB[platform_priority]
