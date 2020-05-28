import unittest2
from mock import Mock, patch
import urllib2

from google.appengine.api import taskqueue
from google.appengine.ext import testbed

from models.notifications.requests.request import Request
from models.notifications.requests.webhook_request import WebhookRequest

from tests.mocks.urllib2.mock_http_error import MockHTTPError
from tests.mocks.notifications.mock_notification import MockNotification


class TestWebhookRequest(unittest2.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_taskqueue_stub(root_path='.')
        self.taskqueue_stub = self.testbed.get_stub(testbed.TASKQUEUE_SERVICE_NAME)

    def tearDown(self):
        self.testbed.deactivate()

    def test_subclass(self):
        request = WebhookRequest(MockNotification(), 'https://www.thebluealliance.com', 'secret')
        self.assertTrue(isinstance(request, Request))

    def test_str(self):
        message_str = WebhookRequest(MockNotification(), 'https://www.thebluealliance.com', 'secret')
        self.assertTrue('WebhookRequest(notification=' in str(message_str))

    def test_webhook_message(self):
        webhook_message_data = {'test': 'something'}
        notification = MockNotification(webhook_message_data=webhook_message_data)
        message = WebhookRequest(notification, 'https://www.thebluealliance.com', 'secret')
        self.assertEqual(message._json_string(), '{"message_data": {"test": "something"}, "message_type": "verification"}')

    def test_webhook_message_no_payload(self):
        notification = MockNotification()
        message = WebhookRequest(notification, 'https://www.thebluealliance.com', 'secret')
        self.assertEqual(message._json_string(), '{"message_type": "verification"}')

    def test_generate_webhook_checksum(self):
        message = WebhookRequest(MockNotification(webhook_message_data={'data': 'value'}), 'https://www.thebluealliance.com', 'secret')
        message_json = message._json_string()
        self.assertEqual(message._generate_webhook_checksum(message_json), 'dbecd85ae53d221c387647085912d2107fa04cd5')

    def test_generate_webhook_checksum_hmac(self):
        message = WebhookRequest(MockNotification(webhook_message_data={'data': 'value'}), 'https://www.thebluealliance.com', 'secret')
        message_json = message._json_string()
        self.assertEqual(message._generate_webhook_hmac(message_json), 'fb2b61d55884a648b35801688754924778b3e71ea2bf8f5effb0f3ffecb5c940')

    def test_generate_webhook_checksum_hmac_unicode_ascii(self):
        message = WebhookRequest(MockNotification(webhook_message_data={'data': 'value'}), 'https://www.thebluealliance.com', unicode('secret'))
        message_json = message._json_string()
        self.assertEqual(message._generate_webhook_hmac(message_json), 'fb2b61d55884a648b35801688754924778b3e71ea2bf8f5effb0f3ffecb5c940')

    def test_generate_webhook_checksum_hmac_unicode_nonascii(self):
        message = WebhookRequest(MockNotification(webhook_message_data={'data': 'value'}), 'https://www.thebluealliance.com', '\x80secret')
        message_json = message._json_string()
        self.assertEqual(message._generate_webhook_hmac(message_json), '2e9e974847184a9f611ed082ba0e76525d1364de520968fbe188737344358d61')

    def test_send_headers(self):
        message = WebhookRequest(MockNotification(webhook_message_data={'data': 'value'}), 'https://www.thebluealliance.com', 'secret')

        with patch.object(urllib2, 'urlopen') as mock_urlopen:
            message.send()
        mock_urlopen.assert_called_once()
        request = mock_urlopen.call_args_list[0][0][0]
        self.assertIsNotNone(request)
        self.assertEqual(request.headers, {'X-tba-checksum': 'dbecd85ae53d221c387647085912d2107fa04cd5', 'Content-type': 'application/json; charset="utf-8"', 'X-tba-hmac': 'fb2b61d55884a648b35801688754924778b3e71ea2bf8f5effb0f3ffecb5c940', 'X-tba-version': '1'})

    def test_send(self):
        message = WebhookRequest(MockNotification(webhook_message_data={'data': 'value'}), 'https://www.thebluealliance.com', 'secret')

        with patch.object(urllib2, 'urlopen') as mock_urlopen, patch.object(message, 'defer_track_notification') as mock_track:
            success = message.send()
        mock_urlopen.assert_called_once()
        mock_track.assert_called_once_with(1)
        self.assertTrue(success)

    def test_send_errors(self):
        message = WebhookRequest(MockNotification(webhook_message_data={'data': 'value'}), 'https://www.thebluealliance.com', 'secret')

        for code in [400, 401, 500]:
            error_mock = Mock()
            error_mock.side_effect = MockHTTPError(code)

            with patch.object(urllib2, 'urlopen', error_mock) as mock_urlopen, patch.object(message, 'defer_track_notification') as mock_track:
                success = message.send()
            mock_urlopen.assert_called_once()
            mock_track.assert_not_called()
            self.assertTrue(success)

    def test_send_error_unknown(self):
        message = WebhookRequest(MockNotification(webhook_message_data={'data': 'value'}), 'https://www.thebluealliance.com', 'secret')

        error_mock = Mock()
        error_mock.side_effect = MockHTTPError(-1)

        with patch.object(urllib2, 'urlopen', error_mock) as mock_urlopen, patch.object(message, 'defer_track_notification') as mock_track:
            success = message.send()
        mock_urlopen.assert_called_once()
        mock_track.assert_not_called()
        self.assertTrue(success)

    def test_send_fail_404(self):
        message = WebhookRequest(MockNotification(webhook_message_data={'data': 'value'}), 'https://www.thebluealliance.com', 'secret')

        error_mock = Mock()
        error_mock.side_effect = MockHTTPError(404)

        with patch.object(urllib2, 'urlopen', error_mock) as mock_urlopen, patch.object(message, 'defer_track_notification') as mock_track:
            success = message.send()
        mock_urlopen.assert_called_once()
        mock_track.assert_not_called()
        self.assertFalse(success)

    def test_send_fail_url_error(self):
        message = WebhookRequest(MockNotification(webhook_message_data={'data': 'value'}), 'https://www.thebluealliance.com', 'secret')

        error_mock = Mock()
        error_mock.side_effect = urllib2.URLError('testing')

        with patch.object(urllib2, 'urlopen', error_mock) as mock_urlopen, patch.object(message, 'defer_track_notification') as mock_track:
            success = message.send()
        mock_urlopen.assert_called_once()
        mock_track.assert_not_called()
        self.assertFalse(success)

    def test_send_fail_deadline_error(self):
        message = WebhookRequest(MockNotification(webhook_message_data={'data': 'value'}), 'https://www.thebluealliance.com', 'secret')

        error_mock = Mock()
        error_mock.side_effect = Exception('Deadline exceeded while waiting for HTTP response from URL: https://thebluealliance.com')

        with patch.object(urllib2, 'urlopen', error_mock) as mock_urlopen, patch.object(message, 'defer_track_notification') as mock_track:
            success = message.send()
        mock_urlopen.assert_called_once()
        mock_track.assert_not_called()
        self.assertTrue(success)

    def test_send_error_other(self):
        message = WebhookRequest(MockNotification(webhook_message_data={'data': 'value'}), 'https://www.thebluealliance.com', 'secret')

        error_mock = Mock()
        error_mock.side_effect = Exception('testing')

        with patch.object(urllib2, 'urlopen', error_mock) as mock_urlopen, patch.object(message, 'defer_track_notification') as mock_track:
            success = message.send()
        mock_urlopen.assert_called_once()
        mock_track.assert_not_called()
        self.assertTrue(success)
