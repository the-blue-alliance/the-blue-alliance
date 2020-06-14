import pytest

from backend.tasks_io.tbans.consts.fcm.platform_priority import PlatformPriority
from backend.tasks_io.tbans.consts.fcm.platform_type import PlatformType


def test_validate_invalid():
    with pytest.raises(ValueError, match="Unsupported platform_priority: 2"):
        PlatformPriority.validate(2)


def test_validate():
    PlatformPriority.validate(PlatformPriority.NORMAL)
    PlatformPriority.validate(PlatformPriority.HIGH)


def test_platform_priority_invalid_platform():
    with pytest.raises(ValueError, match="Unsupported platform_type: -1"):
        PlatformPriority.platform_priority(-1, PlatformPriority.HIGH)


def test_platform_priority_invalid_priority():
    with pytest.raises(ValueError, match="Unsupported platform_priority: -1"):
        PlatformPriority.platform_priority(PlatformType.ANDROID, -1)


def test_platform_priority_android():
    assert (
        PlatformPriority.platform_priority(PlatformType.ANDROID, PlatformPriority.HIGH)
        == "high"
    )
    assert (
        PlatformPriority.platform_priority(
            PlatformType.ANDROID, PlatformPriority.NORMAL
        )
        == "normal"
    )


def test_platform_priority_apns():
    assert (
        PlatformPriority.platform_priority(PlatformType.APNS, PlatformPriority.HIGH)
        == "10"
    )
    assert (
        PlatformPriority.platform_priority(PlatformType.APNS, PlatformPriority.NORMAL)
        == "5"
    )


def test_platform_priority_webpush():
    assert (
        PlatformPriority.platform_priority(PlatformType.WEBPUSH, PlatformPriority.HIGH)
        == "high"
    )
    assert (
        PlatformPriority.platform_priority(
            PlatformType.WEBPUSH, PlatformPriority.NORMAL
        )
        == "normal"
    )
