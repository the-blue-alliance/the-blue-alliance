import unittest2

from tbans.models.subscriptions.subscription_response import SubscriptionResponse

from tests.tbans.mocks.mock_response import MockResponse


class TestSubscriptionResponse(unittest2.TestCase):

    def test_data_response_none_data(self):
        subscription_response = SubscriptionResponse(response=None, error="error")
        self.assertEqual(subscription_response.data, {})

    def test_response_none_status_code(self):
        subscription_response = SubscriptionResponse(response=None, error="error")
        self.assertEqual(subscription_response.error, 'error')
        self.assertEqual(subscription_response.iid_error, 'unknown-error')

    def test_response_content(self):
        response = MockResponse(500, 200)
        with self.assertRaises(TypeError):
            SubscriptionResponse(response=response)

    def test_response_status_code(self):
        response = MockResponse(None, '')
        with self.assertRaises(ValueError):
            SubscriptionResponse(response=response)

    def test_response_status_code_type(self):
        response = MockResponse('', '')
        with self.assertRaises(TypeError):
            SubscriptionResponse(response=response)

    def test_init_error(self):
        response = MockResponse(500, '{"error": "not the same error"}')
        subscription_response = SubscriptionResponse(response=response, error="some error")
        self.assertEqual(subscription_response.error, "some error")
        self.assertEqual(subscription_response.iid_error, "unknown-error")
        self.assertEqual(subscription_response.data, {})

    def test_init_json_error(self):
        response = MockResponse(400, '{"error": "Topic name format is invalid"}')
        subscription_response = SubscriptionResponse(response=response)
        self.assertEqual(subscription_response.error, "Topic name format is invalid")
        self.assertEqual(subscription_response.iid_error, "invalid-argument")
        self.assertEqual(subscription_response.data, {})

    def test_init_error_code(self):
        response = MockResponse(500, '{"error": "InvalidToken"}')
        subscription_response = SubscriptionResponse(response=response)
        self.assertEqual(subscription_response.error, "InvalidToken")
        self.assertEqual(subscription_response.iid_error, "internal-error")
        self.assertEqual(subscription_response.data, {})

    def test_init_multiple_error(self):
        response = MockResponse(500, '{"error": "some json error"}')
        subscription_response = SubscriptionResponse(response=response, error="some error")
        # Should default to passed error
        self.assertEqual(subscription_response.error, "some error")
        self.assertEqual(subscription_response.iid_error, "unknown-error")
        self.assertEqual(subscription_response.data, {})

    def test_init_garbage(self):
        response = MockResponse(200, 'abcd')
        subscription_response = SubscriptionResponse(response=response)
        self.assertEqual(subscription_response.error, None)
        self.assertEqual(subscription_response.iid_error, None)
        self.assertEqual(subscription_response.data, {})

    def test_init(self):
        response = MockResponse(200, '{"applicationVersion": "1.0.2"}')
        subscription_response = SubscriptionResponse(response=response)
        self.assertEqual(subscription_response.error, None)
        self.assertEqual(subscription_response.iid_error, None)
        self.assertEqual(subscription_response.data, {'applicationVersion': '1.0.2'})
