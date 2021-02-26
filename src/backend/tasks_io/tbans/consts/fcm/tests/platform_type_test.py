import pytest

from backend.tasks_io.tbans.consts.fcm.platform_type import PlatformType


def test_validate_invalid():
    with pytest.raises(ValueError, match="Unsupported platform_type: 3"):
        PlatformType.validate(3)


def test_validate():
    PlatformType.validate(PlatformType.ANDROID)
    PlatformType.validate(PlatformType.APNS)
    PlatformType.validate(PlatformType.WEBPUSH)


def test_collapse_key_key_invalid_platform():
    with pytest.raises(ValueError, match="Unsupported platform_type: -1"):
        PlatformType.collapse_key_key(-1)


def test_collapse_key_key():
    assert PlatformType.collapse_key_key(PlatformType.ANDROID) == "collapse_key"
    assert PlatformType.collapse_key_key(PlatformType.APNS) == "apns-collapse-id"
    assert PlatformType.collapse_key_key(PlatformType.WEBPUSH) == "Topic"


def test_priority_key_invalid_platform():
    with pytest.raises(ValueError, match="Unsupported platform_type: -1"):
        PlatformType.priority_key(-1)


def test_priority_key():
    assert PlatformType.priority_key(PlatformType.ANDROID) == "priority"
    assert PlatformType.priority_key(PlatformType.APNS) == "apns-priority"
    assert PlatformType.priority_key(PlatformType.WEBPUSH) == "Urgency"
