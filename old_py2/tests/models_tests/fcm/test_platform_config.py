from firebase_admin import messaging
from mock import patch
import unittest2

from consts.fcm.platform_type import PlatformType
from consts.fcm.platform_priority import PlatformPriority
from models.fcm.platform_config import PlatformConfig


class TestPlatformConfig(unittest2.TestCase):

    def test_str(self):
        payload = PlatformConfig(collapse_key='android_collapse_key', priority=PlatformPriority.NORMAL)
        self.assertEqual(str(payload), 'PlatformConfig(collapse_key="android_collapse_key" priority=0)')

    def test_empty(self):
        PlatformConfig()

    def test_priority_type(self):
        with self.assertRaises(ValueError, msg='Unsupported platform_priority: abc'):
            PlatformConfig(priority='abc')

    def test_priority_supported(self):
        with self.assertRaises(ValueError, msg='Unsupported platform_priority: -1'):
            PlatformConfig(priority=-1)

    def test_platform_config_unsupported_platform_type(self):
        config = PlatformConfig()
        with self.assertRaises(ValueError, msg='Unsupported platform_type: -1'):
            config.platform_config(-1)

    def test_platform_config_unsupported_platform_payload_type(self):
        # Hack this test as if we'd added a new PlatformType but hadn't supported it properly
        config = PlatformConfig()
        with patch.object(PlatformType, '_types', return_value=[-1]), \
        self.assertRaises(ValueError, msg='Unsupported PlatformPayload platform_type: -1'):
            config.platform_config(-1)

    def test_platform_config_android_empty(self):
        config = PlatformConfig()
        android_config = config.platform_config(PlatformType.ANDROID)
        self.assertTrue(isinstance(android_config, messaging.AndroidConfig))
        self.assertIsNone(android_config.collapse_key)
        self.assertIsNone(android_config.priority)

    def test_platform_config_android_collapse_key(self):
        config = PlatformConfig(collapse_key='android_collapse_key')
        android_config = config.platform_config(PlatformType.ANDROID)
        self.assertTrue(isinstance(android_config, messaging.AndroidConfig))
        self.assertEqual(android_config.collapse_key, 'android_collapse_key')
        self.assertIsNone(android_config.priority)

    def test_platform_config_android_priority(self):
        config = PlatformConfig(priority=PlatformPriority.HIGH)
        android_config = config.platform_config(PlatformType.ANDROID)
        self.assertTrue(isinstance(android_config, messaging.AndroidConfig))
        self.assertIsNone(android_config.collapse_key)
        self.assertEqual(android_config.priority, 'high')

    def test_platform_config_android(self):
        config = PlatformConfig(priority=PlatformPriority.NORMAL, collapse_key='collapse_key')
        android_config = config.platform_config(PlatformType.ANDROID)
        self.assertTrue(isinstance(android_config, messaging.AndroidConfig))
        self.assertEqual(android_config.collapse_key, 'collapse_key')
        self.assertEqual(android_config.priority, 'normal')

    def test_platform_config_apns_empty(self):
        config = PlatformConfig()
        apns_config = config.platform_config(PlatformType.APNS)
        self.assertTrue(isinstance(apns_config, messaging.APNSConfig))
        self.assertIsNone(apns_config.headers)
        self.assertTrue(isinstance(apns_config.payload, messaging.APNSPayload))
        self.assertTrue(isinstance(apns_config.payload.aps, messaging.Aps))

    def test_platform_config_apns_collapse_key(self):
        config = PlatformConfig(collapse_key='apns_collapse_key')
        apns_config = config.platform_config(PlatformType.APNS)
        self.assertTrue(isinstance(apns_config, messaging.APNSConfig))
        self.assertEqual(apns_config.headers, {'apns-collapse-id': 'apns_collapse_key'})
        self.assertTrue(isinstance(apns_config.payload, messaging.APNSPayload))
        self.assertTrue(isinstance(apns_config.payload.aps, messaging.Aps))

    def test_platform_config_apns_priority(self):
        config = PlatformConfig(priority=PlatformPriority.HIGH)
        apns_config = config.platform_config(PlatformType.APNS)
        self.assertTrue(isinstance(apns_config, messaging.APNSConfig))
        self.assertEqual(apns_config.headers, {'apns-priority': '10'})
        self.assertTrue(isinstance(apns_config.payload, messaging.APNSPayload))
        self.assertTrue(isinstance(apns_config.payload.aps, messaging.Aps))

    def test_platform_config_apns(self):
        config = PlatformConfig(priority=PlatformPriority.NORMAL, collapse_key='collapse_key')
        apns_config = config.platform_config(PlatformType.APNS)
        self.assertTrue(isinstance(apns_config, messaging.APNSConfig))
        self.assertEqual(apns_config.headers, {'apns-collapse-id': 'collapse_key', 'apns-priority': '5'})
        self.assertTrue(isinstance(apns_config.payload, messaging.APNSPayload))
        self.assertTrue(isinstance(apns_config.payload.aps, messaging.Aps))

    def test_platform_config_webpush_empty(self):
        config = PlatformConfig()
        webpush_config = config.platform_config(PlatformType.WEBPUSH)
        self.assertTrue(isinstance(webpush_config, messaging.WebpushConfig))
        self.assertIsNone(webpush_config.headers)

    def test_platform_config_webpush_collapse_key(self):
        config = PlatformConfig(collapse_key='webpush_collapse_key')
        webpush_config = config.platform_config(PlatformType.WEBPUSH)
        self.assertTrue(isinstance(webpush_config, messaging.WebpushConfig))
        self.assertEqual(webpush_config.headers, {'Topic': 'webpush_collapse_key'})

    def test_platform_config_webpush_priority(self):
        config = PlatformConfig(priority=PlatformPriority.HIGH)
        webpush_config = config.platform_config(PlatformType.WEBPUSH)
        self.assertTrue(isinstance(webpush_config, messaging.WebpushConfig))
        self.assertEqual(webpush_config.headers, {'Urgency': 'high'})

    def test_platform_config_webpush(self):
        config = PlatformConfig(priority=PlatformPriority.NORMAL, collapse_key='collapse_key')
        webpush_config = config.platform_config(PlatformType.WEBPUSH)
        self.assertTrue(isinstance(webpush_config, messaging.WebpushConfig))
        self.assertEqual(webpush_config.headers, {'Topic': 'collapse_key', 'Urgency': 'normal'})
