from unittest.mock import patch

import pytest
from firebase_admin import messaging

from backend.tasks_io.tbans.consts.fcm.platform_priority import PlatformPriority
from backend.tasks_io.tbans.consts.fcm.platform_type import PlatformType
from backend.tasks_io.tbans.models.fcm.platform_config import PlatformConfig


def test_str():
    payload = PlatformConfig(
        collapse_key="android_collapse_key", priority=PlatformPriority.NORMAL
    )
    assert (
        str(payload) == 'PlatformConfig(collapse_key="android_collapse_key" priority=0)'
    )


def test_empty():
    PlatformConfig()


def test_priority_type():
    with pytest.raises(ValueError, match="Unsupported platform_priority: abc"):
        PlatformConfig(priority="abc")


def test_priority_supported():
    with pytest.raises(ValueError, match="Unsupported platform_priority: -1"):
        PlatformConfig(priority=-1)


def test_platform_config_unsupported_platform_type():
    config = PlatformConfig()
    with pytest.raises(ValueError, match="Unsupported platform_type: -1"):
        config.platform_config(-1)


def test_platform_config_unsupported_platform_payload_type():
    # Hack this test as if we'd added a new PlatformType but hadn't supported it properly
    config = PlatformConfig()
    with patch.object(PlatformType, "validate"), pytest.raises(
        TypeError, match="Unsupported PlatformPayload platform_type: -1"
    ):
        config.platform_config(-1)


def test_platform_config_android_empty():
    config = PlatformConfig()
    android_config = config.platform_config(PlatformType.ANDROID)
    assert isinstance(android_config, messaging.AndroidConfig)
    assert android_config.collapse_key is None
    assert android_config.priority is None


def test_platform_config_android_collapse_key():
    config = PlatformConfig(collapse_key="android_collapse_key")
    android_config = config.platform_config(PlatformType.ANDROID)
    assert isinstance(android_config, messaging.AndroidConfig)
    assert android_config.collapse_key == "android_collapse_key"
    assert android_config.priority is None


def test_platform_config_android_priority():
    config = PlatformConfig(priority=PlatformPriority.HIGH)
    android_config = config.platform_config(PlatformType.ANDROID)
    assert isinstance(android_config, messaging.AndroidConfig)
    assert android_config.collapse_key is None
    assert android_config.priority == "high"


def test_platform_config_android():
    config = PlatformConfig(
        priority=PlatformPriority.NORMAL, collapse_key="collapse_key"
    )
    android_config = config.platform_config(PlatformType.ANDROID)
    assert isinstance(android_config, messaging.AndroidConfig)
    assert android_config.collapse_key == "collapse_key"
    assert android_config.priority == "normal"


def test_platform_config_apns_empty():
    config = PlatformConfig()
    apns_config = config.platform_config(PlatformType.APNS)
    assert isinstance(apns_config, messaging.APNSConfig)
    assert apns_config.headers is None
    assert isinstance(apns_config.payload, messaging.APNSPayload)
    assert isinstance(apns_config.payload.aps, messaging.Aps)


def test_platform_config_apns_collapse_key():
    config = PlatformConfig(collapse_key="apns_collapse_key")
    apns_config = config.platform_config(PlatformType.APNS)
    assert isinstance(apns_config, messaging.APNSConfig)
    assert apns_config.headers == {"apns-collapse-id": "apns_collapse_key"}
    assert isinstance(apns_config.payload, messaging.APNSPayload)
    assert isinstance(apns_config.payload.aps, messaging.Aps)


def test_platform_config_apns_priority():
    config = PlatformConfig(priority=PlatformPriority.HIGH)
    apns_config = config.platform_config(PlatformType.APNS)
    assert isinstance(apns_config, messaging.APNSConfig)
    assert apns_config.headers == {"apns-priority": "10"}
    assert isinstance(apns_config.payload, messaging.APNSPayload)
    assert isinstance(apns_config.payload.aps, messaging.Aps)


def test_platform_config_apns():
    config = PlatformConfig(
        priority=PlatformPriority.NORMAL, collapse_key="collapse_key"
    )
    apns_config = config.platform_config(PlatformType.APNS)
    assert isinstance(apns_config, messaging.APNSConfig)
    assert apns_config.headers == {
        "apns-collapse-id": "collapse_key",
        "apns-priority": "5",
    }
    assert isinstance(apns_config.payload, messaging.APNSPayload)
    assert isinstance(apns_config.payload.aps, messaging.Aps)


def test_platform_config_webpush_empty():
    config = PlatformConfig()
    webpush_config = config.platform_config(PlatformType.WEBPUSH)
    assert isinstance(webpush_config, messaging.WebpushConfig)
    assert webpush_config.headers is None


def test_platform_config_webpush_collapse_key():
    config = PlatformConfig(collapse_key="webpush_collapse_key")
    webpush_config = config.platform_config(PlatformType.WEBPUSH)
    assert isinstance(webpush_config, messaging.WebpushConfig)
    assert webpush_config.headers == {"Topic": "webpush_collapse_key"}


def test_platform_config_webpush_priority():
    config = PlatformConfig(priority=PlatformPriority.HIGH)
    webpush_config = config.platform_config(PlatformType.WEBPUSH)
    assert isinstance(webpush_config, messaging.WebpushConfig)
    assert webpush_config.headers == {"Urgency": "high"}


def test_platform_config_webpush():
    config = PlatformConfig(
        priority=PlatformPriority.NORMAL, collapse_key="collapse_key"
    )
    webpush_config = config.platform_config(PlatformType.WEBPUSH)
    assert isinstance(webpush_config, messaging.WebpushConfig)
    assert webpush_config.headers == {"Topic": "collapse_key", "Urgency": "normal"}
