from __future__ import annotations

import enum
from typing import Dict, Set


@enum.unique
class ClientType(enum.IntEnum):
    # Operating System types for MobileClient.client_type
    OS_ANDROID = 0
    OS_IOS = 1
    WEBHOOK = 2
    WEB = 3
    TEST = 4


FCM_CLIENTS: Set[ClientType] = {
    ClientType.OS_IOS,
    ClientType.WEB,
}


NAMES: Dict[ClientType, str] = {
    ClientType.OS_ANDROID: "Android",
    ClientType.OS_IOS: "iOS",
    ClientType.WEBHOOK: "Webhook",
    ClientType.WEB: "Web",
    ClientType.TEST: "Test",
}

ENUMS: Dict[str, ClientType] = {
    "android": ClientType.OS_ANDROID,
    "ios": ClientType.OS_IOS,
    "webhook": ClientType.WEBHOOK,
    "web": ClientType.WEB,
    "test": ClientType.TEST,
}
