import unittest2

from consts.fcm.platform_type import PlatformType


class TestPlatformType(unittest2.TestCase):

    def test_validate_invalid(self):
        with self.assertRaises(ValueError):
            PlatformType.validate(3)

    def test_validate(self):
        PlatformType.validate(PlatformType.ANDROID)
        PlatformType.validate(PlatformType.APNS)
        PlatformType.validate(PlatformType.WEBPUSH)

    def test_collapse_key_key_invalid_platform(self):
        with self.assertRaises(ValueError):
            PlatformType.collapse_key_key(-1)

    def test_collapse_key_key(self):
        self.assertEqual(PlatformType.collapse_key_key(PlatformType.ANDROID), 'collapse_key')
        self.assertEqual(PlatformType.collapse_key_key(PlatformType.APNS), 'apns-collapse-id')
        self.assertEqual(PlatformType.collapse_key_key(PlatformType.WEBPUSH), 'Topic')

    def test_priority_key_invalid_platform(self):
        with self.assertRaises(ValueError):
            PlatformType.priority_key(-1)

    def test_priority_key(self):
        self.assertEqual(PlatformType.priority_key(PlatformType.ANDROID), 'priority')
        self.assertEqual(PlatformType.priority_key(PlatformType.APNS), 'apns-priority')
        self.assertEqual(PlatformType.priority_key(PlatformType.WEBPUSH), 'Urgency')
