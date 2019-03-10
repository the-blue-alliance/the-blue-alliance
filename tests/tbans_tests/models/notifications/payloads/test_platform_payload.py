import unittest2

from tbans.consts.platform_payload_type import PlatformPayloadType
from tbans.consts.platform_payload_priority import PlatformPayloadPriority
from tbans.models.notifications.payloads.platform_payload import PlatformPayload


class TestPlatformPayload(unittest2.TestCase):

    def test_str(self):
        payload = PlatformPayload(platform_type=PlatformPayloadType.ANDROID, priority=PlatformPayloadPriority.NORMAL, collapse_key='android_collapse_key')

    def test_str_partial(self):
        payload = PlatformPayload(priority=PlatformPayloadPriority.NORMAL, collapse_key='android_collapse_key')
        self.assertEqual(str(payload), 'PlatformPayload(platform_type=None priority=0 collapse_key="android_collapse_key")')

    def test_platform_type_empty(self):
        PlatformPayload()

    def test_platform_type_type(self):
        with self.assertRaises(TypeError):
            PlatformPayload(platform_type='abc')

    def test_platform_type_supported(self):
        with self.assertRaises(TypeError):
            PlatformPayload(platform_type=200)

    def test_priority_type(self):
        with self.assertRaises(TypeError):
            PlatformPayload(priority='abc')

    def test_priority_supported(self):
        with self.assertRaises(TypeError):
            PlatformPayload(priority='abc')

    def test_collapse_key_type(self):
        with self.assertRaises(TypeError):
            PlatformPayload(collapse_key=True)

    def test_validate_platform_type(self):
        PlatformPayload._validate_platform_type(PlatformPayloadType.APNS)

    def test_validate_platform_type_unsupported(self):
        with self.assertRaises(TypeError):
            PlatformPayload._validate_platform_type(200)

    def test_platform_payload_dict_unsupported(self):
        payload = PlatformPayload()
        with self.assertRaises(TypeError):
            payload.platform_payload_dict(200)

    def test_platform_payload_empty(self):
        payload = PlatformPayload(platform_type=PlatformPayloadType.ANDROID)
        self.assertIsNone(payload.payload_dict)

    def test_platform_payload_dict(self):
        payload = PlatformPayload(platform_type=PlatformPayloadType.ANDROID, priority=PlatformPayloadPriority.NORMAL, collapse_key='android_collapse_key')
        self.assertNotEqual(payload.payload_dict, payload.platform_payload_dict(PlatformPayloadType.APNS))

    def test_platform_payload_android(self):
        payload = PlatformPayload(platform_type=PlatformPayloadType.ANDROID, priority=PlatformPayloadPriority.NORMAL, collapse_key='android_collapse_key')
        self.assertEqual(payload.payload_dict, {'priority': 'NORMAL', 'collapse_key': 'android_collapse_key'})
        self.assertEqual(payload.payload_dict, payload.platform_payload_dict(PlatformPayloadType.ANDROID))

    def test_platform_payload_apns(self):
        payload = PlatformPayload(platform_type=PlatformPayloadType.APNS, priority=PlatformPayloadPriority.NORMAL, collapse_key='ios_collapse_key')
        self.assertEqual(payload.payload_dict, {'apns-priority': '5', 'apns-collapse-id': 'ios_collapse_key'})
        self.assertEqual(payload.payload_dict, payload.platform_payload_dict(PlatformPayloadType.APNS))

    def test_platform_payload_webpush(self):
        payload = PlatformPayload(platform_type=PlatformPayloadType.WEBPUSH, priority=PlatformPayloadPriority.NORMAL, collapse_key='web_collapse_key')
        self.assertEqual(payload.payload_dict, {'Urgency': 'normal', 'Topic': 'web_collapse_key'})
        self.assertEqual(payload.payload_dict, payload.platform_payload_dict(PlatformPayloadType.WEBPUSH))
