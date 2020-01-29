import unittest2

from consts.fcm.platform_priority import PlatformPriority
from consts.fcm.platform_type import PlatformType


class TestPlatformPriority(unittest2.TestCase):

    def test_validate_invalid(self):
        with self.assertRaises(ValueError):
            PlatformPriority.validate(2)

    def test_validate(self):
        PlatformPriority.validate(PlatformPriority.NORMAL)
        PlatformPriority.validate(PlatformPriority.HIGH)

    def test_platform_priority_invalid_platform(self):
        with self.assertRaises(ValueError):
            PlatformPriority.platform_priority(-1, PlatformPriority.HIGH)

    def test_platform_priority_invalid_priority(self):
        with self.assertRaises(ValueError):
            PlatformPriority.platform_priority(PlatformType.ANDROID, -1)

    def test_platform_priority_android(self):
        self.assertEqual(PlatformPriority.platform_priority(PlatformType.ANDROID, PlatformPriority.HIGH), 'high')
        self.assertEqual(PlatformPriority.platform_priority(PlatformType.ANDROID, PlatformPriority.NORMAL), 'normal')

    def test_platform_priority_apns(self):
        self.assertEqual(PlatformPriority.platform_priority(PlatformType.APNS, PlatformPriority.HIGH), '10')
        self.assertEqual(PlatformPriority.platform_priority(PlatformType.APNS, PlatformPriority.NORMAL), '5')

    def test_platform_priority_webpush(self):
        self.assertEqual(PlatformPriority.platform_priority(PlatformType.WEBPUSH, PlatformPriority.HIGH), 'high')
        self.assertEqual(PlatformPriority.platform_priority(PlatformType.WEBPUSH, PlatformPriority.NORMAL), 'normal')
