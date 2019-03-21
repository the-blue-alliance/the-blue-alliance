import unittest2

from tbans.models.requests.subscriptions.subscription_status_response import SubscriptionStatusResponse

from tests.tbans_tests.mocks.mock_response import MockResponse


class TestSubscriptionStatusResponse(unittest2.TestCase):

    def test_init_wrong_rel(self):
        response = MockResponse(200, '{"rel":"abc"}')
        with self.assertRaises(TypeError):
            SubscriptionStatusResponse(response=response)

    def test_init_rel_empty(self):
        response = MockResponse(200, '{"rel":{}}')
        SubscriptionStatusResponse(response=response)

    def test_init_topics_type(self):
        response = MockResponse(200, '{"rel":{"topics": "abc"}}')
        with self.assertRaises(TypeError):
            SubscriptionStatusResponse(response=response)

    def test_init_topics_empty(self):
        response = MockResponse(200, '{"rel":{"topics": {}}}')
        SubscriptionStatusResponse(response=response)

    def test_init_topics(self):
        response = MockResponse(200, '{"rel":{"topics":{"broadcasts":{"addDate":"2019-02-15"}}}}')
        subscription_status = SubscriptionStatusResponse(response=response)
        self.assertEqual(subscription_status.error, None)
        self.assertEqual(subscription_status.subscriptions, ["broadcasts"])

    def test_init_garbage(self):
        response = MockResponse(200, 'abcd')
        subscription_status = SubscriptionStatusResponse(response=response)
        self.assertEqual(subscription_status.error, None)
        self.assertEqual(subscription_status.subscriptions, [])

    def test_str(self):
        response = MockResponse(200, '{"rel":{"topics":{"broadcasts":{"addDate":"2019-02-15"}}}}')
        subscription_status = SubscriptionStatusResponse(response=response)
        self.assertEqual(str(subscription_status), "SubscriptionStatusResponse(subscriptions=['broadcasts'], iid_error=None, error=None)")

    def test_str_error(self):
        response = MockResponse(400, '{"error":"some error"}')
        subscription_status = SubscriptionStatusResponse(response=response)
        self.assertEqual(str(subscription_status), "SubscriptionStatusResponse(subscriptions=[], iid_error=invalid-argument, error=some error)")

    def test_error(self):
        response = MockResponse(400, '{"error":"some error"}')
        subscription_status = SubscriptionStatusResponse(response=response)
        self.assertEqual(subscription_status.error, "some error")
        self.assertEqual(subscription_status.subscriptions, [])
