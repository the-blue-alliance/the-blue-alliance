import unittest2

from google.appengine.ext import testbed

from tbans.models.requests.notifications.notification_request import NotificationRequest
from tbans.models.requests.notifications.webhook_request import WebhookRequest

from tests.tbans_tests.mocks.notifications.mock_notification import MockNotification


class TestWebhookRequest(unittest2.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_urlfetch_stub(urlmatchers=[(lambda url: True, self._stub_webhook_request)])

    def tearDown(self):
        self.testbed.deactivate()

    def _stub_webhook_request(self, url, payload, method, headers, request, response, follow_redirects=False, deadline=None, validate_certificate=None, http_proxy=None):
        # While we're here - check that our request looks right
        self.assertEqual(url, 'https://www.thebluealliance.com/')
        self.assertEqual({header.key(): header.value() for header in headers}, {'X-TBA-Checksum': 'dbecd85ae53d221c387647085912d2107fa04cd5', 'Content-Type': 'application/json', 'X-TBA-Version': '1'})
        self.assertEqual(payload, '{"message_data": {"data": "value"}, "message_type": "verification"}')
        self.assertEqual(method, 'POST')
        response.set_statuscode(200)
        response.set_content('Some content here')

    def test_subclass(self):
        request = WebhookRequest(MockNotification(), 'https://www.thebluealliance.com/', 'secret')
        self.assertTrue(isinstance(request, NotificationRequest))

    def test_url(self):
        with self.assertRaises(TypeError):
            WebhookRequest(MockNotification(), None, 'secret')

    def test_url_type(self):
        with self.assertRaises(TypeError):
            WebhookRequest(MockNotification(), 200, 'secret')

    def test_url_empty(self):
        with self.assertRaises(ValueError):
            WebhookRequest(MockNotification(), '', 'secret')

    def test_secret(self):
        with self.assertRaises(TypeError):
            WebhookRequest(MockNotification(), 'https://www.thebluealliance.com/', None)

    def test_secret_type(self):
        with self.assertRaises(TypeError):
            WebhookRequest(MockNotification(), 'https://www.thebluealliance.com/', 200)

    def test_secret_empty(self):
        with self.assertRaises(ValueError):
            WebhookRequest(MockNotification(), 'https://www.thebluealliance.com/', '')

    def test_str(self):
        message_str = WebhookRequest(MockNotification(), 'https://www.thebluealliance.com/', 'secret')
        self.assertTrue('WebhookRequest(notification=' in str(message_str))

    def test_webhook_message(self):
        webhook_payload = {'test': 'something'}
        notification = MockNotification(webhook_payload=webhook_payload)
        message = WebhookRequest(notification, 'https://www.thebluealliance.com/', 'secret')
        self.assertEqual(message.json_string(), '{"message_data": {"test": "something"}, "message_type": "verification"}')

    def test_webhook_message_no_payload(self):
        notification = MockNotification()
        message = WebhookRequest(notification, 'https://www.thebluealliance.com/', 'secret')
        self.assertEqual(message.json_string(), '{"message_type": "verification"}')

    def test_generate_webhook_checksum(self):
        message = WebhookRequest(MockNotification(webhook_payload={'data': 'value'}), 'https://www.thebluealliance.com/', 'secret')
        message_json = message.json_string()
        self.assertEqual(message._generate_webhook_checksum(message_json), 'dbecd85ae53d221c387647085912d2107fa04cd5')

    def test_send(self):
        message = WebhookRequest(MockNotification(webhook_payload={'data': 'value'}), 'https://www.thebluealliance.com/', 'secret')
        response = message.send()
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.content)
