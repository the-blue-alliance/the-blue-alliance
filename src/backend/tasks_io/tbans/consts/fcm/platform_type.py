from __future__ import annotations

import enum
from typing import Dict


@enum.unique
class PlatformType(enum.IntEnum):
    """
    Constants for the type of FCM platforms.
    https://firebase.google.com/docs/reference/fcm/rest/v1/projects.messages
    """

    ANDROID = 0
    APNS = 1
    WEBPUSH = 2

    @staticmethod
    def validate(platform_type: PlatformType) -> None:
        """ Validate that the platform_type is supported.

        Raises:
            ValueError: If platform_type is an unsupported platform type.
        """
        if platform_type not in list(PlatformType):
            raise ValueError("Unsupported platform_type: {}".format(platform_type))

    @staticmethod
    def collapse_key_key(platform_type: PlatformType) -> str:
        # Validate that platform_type is supported
        PlatformType.validate(platform_type)

        COLLAPSE_KEY_KEYS: Dict[PlatformType, str] = {
            PlatformType.ANDROID: "collapse_key",
            PlatformType.APNS: "apns-collapse-id",
            PlatformType.WEBPUSH: "Topic",
        }
        return COLLAPSE_KEY_KEYS[platform_type]

    @staticmethod
    def priority_key(platform_type: PlatformType) -> str:
        # Validate that platform_type is supported
        PlatformType.validate(platform_type)

        PRIORITY_KEYS: Dict[PlatformType, str] = {
            PlatformType.ANDROID: "priority",
            PlatformType.APNS: "apns-priority",
            PlatformType.WEBPUSH: "Urgency",
        }
        return PRIORITY_KEYS[platform_type]
