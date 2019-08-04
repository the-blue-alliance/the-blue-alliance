from firebase_admin import messaging
import unittest2

from tbans.consts.fcm.platform_type import PlatformType
from tbans.consts.fcm.platform_priority import PlatformPriority
from tbans.models.fcm.platform_config import PlatformConfig


class TestPlatformConfig(unittest2.TestCase):

    def test_str(self):
        payload = PlatformConfig(collapse_key='android_collapse_key', priority=PlatformPriority.NORMAL)
        self.assertEqual(str(payload), 'PlatformConfig(collapse_key="android_collapse_key" priority=0)')

    def test_empty(self):
        PlatformConfig()

    def test_collapse_key_type(self):
        with self.assertRaises(TypeError):
            PlatformConfig(collapse_key=True)

    def test_priority_type(self):
        with self.assertRaises(TypeError):
            PlatformConfig(priority='abc')

    def test_priority_supported(self):
        with self.assertRaises(ValueError):
            PlatformConfig(priority=-1)

    def test_platform_config_unsupported(self):
        config = PlatformConfig()
        with self.assertRaises(ValueError):
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
        self.assertEqual(android_config.priority, 'HIGH')

    def test_platform_config_android(self):
        config = PlatformConfig(priority=PlatformPriority.NORMAL, collapse_key='collapse_key')
        android_config = config.platform_config(PlatformType.ANDROID)
        self.assertTrue(isinstance(android_config, messaging.AndroidConfig))
        self.assertEqual(android_config.collapse_key, 'collapse_key')
        self.assertEqual(android_config.priority, 'NORMAL')

    def test_platform_config_apns_empty(self):
        config = PlatformConfig()
        apns_config = config.platform_config(PlatformType.APNS)
        self.assertTrue(isinstance(apns_config, messaging.APNSConfig))
        self.assertIsNone(apns_config.headers)
        self.assertIsNone(apns_config.payload)

    def test_platform_config_apns_collapse_key(self):
        config = PlatformConfig(collapse_key='apns_collapse_key')
        apns_config = config.platform_config(PlatformType.APNS)
        self.assertTrue(isinstance(apns_config, messaging.APNSConfig))
        self.assertEqual(apns_config.headers, {'apns-collapse-id': 'apns_collapse_key'})
        self.assertTrue(isinstance(apns_config.payload, messaging.APNSPayload))
        self.assertTrue(isinstance(apns_config.payload.aps, messaging.Aps))
        self.assertTrue(apns_config.payload.aps.content_available)

    def test_platform_config_apns_priority(self):
        config = PlatformConfig(priority=PlatformPriority.HIGH)
        apns_config = config.platform_config(PlatformType.APNS)
        self.assertTrue(isinstance(apns_config, messaging.APNSConfig))
        self.assertEqual(apns_config.headers, {'apns-priority': '10'})
        self.assertTrue(isinstance(apns_config.payload, messaging.APNSPayload))
        self.assertTrue(isinstance(apns_config.payload.aps, messaging.Aps))
        self.assertTrue(apns_config.payload.aps.content_available)

    def test_platform_config_apns(self):
        config = PlatformConfig(priority=PlatformPriority.NORMAL, collapse_key='collapse_key')
        apns_config = config.platform_config(PlatformType.APNS)
        self.assertTrue(isinstance(apns_config, messaging.APNSConfig))
        self.assertEqual(apns_config.headers, {'apns-collapse-id': 'collapse_key', 'apns-priority': '5'})
        self.assertTrue(isinstance(apns_config.payload, messaging.APNSPayload))
        self.assertTrue(isinstance(apns_config.payload.aps, messaging.Aps))
        self.assertTrue(apns_config.payload.aps.content_available)

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
