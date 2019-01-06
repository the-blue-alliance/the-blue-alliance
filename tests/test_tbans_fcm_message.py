import unittest2

from google.appengine.ext import testbed

from consts.notification_type import NotificationType
from tbans.consts.platform_payload_priority import PlatformPayloadPriority
from tbans.consts.platform_payload_type import PlatformPayloadType
from tbans.models.messages.fcm_message import FCMMessage
from tbans.models.messages.message import Message
from tbans.models.notifications.notification import Notification
from tbans.models.notifications.payloads.payload import Payload
from tbans.models.notifications.payloads.notification_payload import NotificationPayload
from tbans.models.notifications.payloads.platform_payload import PlatformPayload

from tests.mock_notification import MockNotification
from tests.mock_payload import MockPayload


class TestFCMMessage(unittest2.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_app_identity_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_urlfetch_stub(urlmatchers=[(lambda url: True, self._stub_fcm_request)])

    def tearDown(self):
        self.testbed.deactivate()

    def _stub_fcm_request(self, url, payload, method, headers, request, response, follow_redirects=False, deadline=None, validate_certificate=None, http_proxy=None):
        # While we're here - check that our request looks right
        self.assertEqual(url, 'https://fcm.googleapis.com/v1/projects/testbed-test/messages:send')

        # Test headers - kinda weird though, since our Auth header will change between tests
        # We need to make sure that we have an Auth header, but we don't care what it is
        headers = {header.key(): header.value() for header in headers}
        authorization_header = headers.get('Authorization', None)
        del headers['Authorization']
        self.assertEqual(headers, {'Content-Type': 'application/json'})
        self.assertIsNotNone(authorization_header)

        self.assertEqual(payload, '{"message": {"token": "abc", "data": {"message_type": "verification"}}}')
        self.assertEqual(method, 'POST')
        response.set_statuscode(200)
        response.set_content('Some content here')

    def test_subclass(self):
        message = FCMMessage(MockNotification(), token='abcd')
        self.assertTrue(isinstance(message, Message))

    def test_init_delivery_none(self):
        with self.assertRaises(TypeError):
            FCMMessage(notification=MockNotification())

    def test_init_delivery_multiple(self):
        with self.assertRaises(TypeError):
            FCMMessage(notification=MockNotification(), token='abc', topic='def')

    def test_set_payload(self):
        data = {}

        FCMMessage._set_payload(data, 'test', None)
        self.assertEqual(data.get('test', 'test-default'), 'test-default')

        data_payload = {'data': 'some_data'}
        FCMMessage._set_payload(data, 'test', MockPayload(data_payload))
        self.assertEqual(data.get('test', 'test-default'), data_payload)

    def test_set_platform_payload(self):
        data = {}

        platform_payload = PlatformPayload(priority=PlatformPayloadPriority.HIGH, collapse_key='collapse_key')
        apns_payload = PlatformPayload(platform_type=PlatformPayloadType.APNS, priority=PlatformPayloadPriority.NORMAL, collapse_key='different_collapse_key')

        notification = MockNotification(platform_payload=platform_payload)
        FCMMessage._set_platform_payload(data, PlatformPayloadType.APNS, notification.apns_payload, notification.platform_payload)
        self.assertEqual(data, {'apns': {'apns-collapse-id': 'collapse_key', 'apns-priority': '10'}})

    def test_set_platform_payload_override(self):
        data = {}

        platform_payload = PlatformPayload(priority=PlatformPayloadPriority.HIGH, collapse_key='collapse_key')
        apns_payload = PlatformPayload(platform_type=PlatformPayloadType.APNS, priority=PlatformPayloadPriority.NORMAL, collapse_key='different_collapse_key')

        notification = MockNotification(platform_payload=platform_payload, apns_payload=apns_payload)
        FCMMessage._set_platform_payload(data, PlatformPayloadType.APNS, notification.apns_payload, notification.platform_payload)
        self.assertEqual(data, {'apns': {'apns-collapse-id': 'different_collapse_key', 'apns-priority': '5'}})

    def test_json_string_token(self):
        message = FCMMessage(MockNotification(), token='abcd')
        self.assertEqual(message.json_string(), '{"message": {"token": "abcd", "data": {"message_type": "verification"}}}')

    def test_json_string_topic(self):
        message = FCMMessage(MockNotification(), topic='abcd')
        self.assertEqual(message.json_string(), '{"message": {"topic": "abcd", "data": {"message_type": "verification"}}}')

    def test_json_string_condition(self):
        message = FCMMessage(MockNotification(), condition="\'dogs\' in topics")
        self.assertEqual(message.json_string(), '{"message": {"data": {"message_type": "verification"}, "condition": "\'dogs\' in topics"}}')

    def test_json_string_data_payload(self):
        message = FCMMessage(MockNotification(data_payload={"verification": "some_code"}), token='abc')
        self.assertEqual(message.json_string(), '{"message": {"token": "abc", "data": {"message_type": "verification", "verification": "some_code"}}}')

    def test_json_string_notification_payload(self):
        message = FCMMessage(MockNotification(notification_payload=NotificationPayload(title='Title Here', body='Body here')), token='abc')
        self.assertEqual(message.json_string(), '{"message": {"notification": {"body": "Body here", "title": "Title Here"}, "token": "abc", "data": {"message_type": "verification"}}}')

    def test_json_string_platform_payload(self):
        message = FCMMessage(MockNotification(platform_payload=PlatformPayload(priority=PlatformPayloadPriority.HIGH, collapse_key='collapse_key')), token='abc')
        self.assertEqual(message.json_string(), '{"message": {"apns": {"apns-collapse-id": "collapse_key", "apns-priority": "10"}, "token": "abc", "data": {"message_type": "verification"}, "android": {"priority": "HIGH", "collapse_key": "collapse_key"}, "webpush": {"Topic": "collapse_key", "Urgency": "high"}}}')

    def test_json_string_platform_payload_override(self):
        platform_payload = PlatformPayload(priority=PlatformPayloadPriority.HIGH, collapse_key='collapse_key')
        apns_payload = PlatformPayload(platform_type=PlatformPayloadType.APNS, priority=PlatformPayloadPriority.NORMAL, collapse_key='different_collapse_key')
        message = FCMMessage(MockNotification(platform_payload=platform_payload, apns_payload=apns_payload), token='abc')
        self.assertEqual(message.json_string(), '{"message": {"apns": {"apns-collapse-id": "different_collapse_key", "apns-priority": "5"}, "token": "abc", "data": {"message_type": "verification"}, "android": {"priority": "HIGH", "collapse_key": "collapse_key"}, "webpush": {"Topic": "collapse_key", "Urgency": "high"}}}')

    def test_delivery_option_token(self):
        message = FCMMessage(MockNotification(), token='abc')
        delivery_option = message._delivery_option()
        self.assertEqual(delivery_option[0], 'token')
        self.assertEqual(delivery_option[1], 'abc')

    def test_delivery_option_token(self):
        message = FCMMessage(MockNotification(), topic='def')
        delivery_option = message._delivery_option()
        self.assertEqual(delivery_option[0], 'topic')
        self.assertEqual(delivery_option[1], 'def')

    def test_delivery_option_token(self):
        message = FCMMessage(MockNotification(), condition='ghi')
        delivery_option = message._delivery_option()
        self.assertEqual(delivery_option[0], 'condition')
        self.assertEqual(delivery_option[1], 'ghi')

    def test_str_token(self):
        message = FCMMessage(MockNotification(), token='abc')
        self.assertTrue('FCMMessage(token="abc", notification=' in str(message))

    def test_str_topic(self):
        message = FCMMessage(MockNotification(), topic='def')
        self.assertTrue('FCMMessage(topic="def", notification=' in str(message))

    def test_str_condition(self):
        message = FCMMessage(MockNotification(), condition='hij')
        self.assertTrue('FCMMessage(condition="hij", notification=' in str(message))

    def test_fcm_url(self):
        message = FCMMessage(MockNotification(), token='abc')
        self.assertEqual(message._fcm_url, 'https://fcm.googleapis.com/v1/projects/testbed-test/messages:send')

    def test_get_access_token(self):
        self.assertIsNotNone(FCMMessage._get_access_token())

    def test_send(self):
        message = FCMMessage(notification=MockNotification(), token='abc')
        response = message.send()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, 'Some content here')

    def test_transform_fcm_response_success(self):
        _status_code = 200
        _content = '{"name": "projects/testbed-test/messages/1545762214218984"}'
        response = MockResponse(_status_code, _content)
        transformed_response = FCMMessage._transform_fcm_response(response)
        self.assertEqual(transformed_response.status_code, _status_code)
        self.assertEqual(transformed_response.content, _content)

    def test_transform_fcm_response_error(self):
        _status_code = 404
        _content = '{"error": {"code": 404,"message": "Requested entity was not found.","status": "NOT_FOUND","details": [{"@type": "type.googleapis.com/google.firebase.fcm.v1.FcmError","errorCode": "UNREGISTERED"}]}}'
        response = MockResponse(_status_code, _content)
        transformed_response = FCMMessage._transform_fcm_response(response)
        self.assertEqual(transformed_response.status_code, _status_code)
        self.assertEqual(transformed_response.content, 'registration-token-not-registered')


class MockResponse(object):

    def __init__(self, status_code, content):
        self.status_code = status_code
        self.content = content
