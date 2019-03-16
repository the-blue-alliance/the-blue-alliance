import unittest2

from tbans.models.subscriptions.subscription_status import SubscriptionStatus

from tests.tbans_tests.mocks.mock_response import MockResponse


class TestSubscriptionStatus(unittest2.TestCase):

    def test_init_wrong_rel(self):
        response = MockResponse(200, '{"rel":"abc"}')
        with self.assertRaises(ValueError):
            SubscriptionStatus(response=response)

    def test_init_wrong_topics(self):
        response = MockResponse(200, '{"rel":{"topics": "abc"}}')
        with self.assertRaises(ValueError):
            SubscriptionStatus(response=response)

    def test_init_topics(self):
        response = MockResponse(200, '{"rel":{"topics":{"broadcasts":{"addDate":"2019-02-15"}}}}')
        subscription_status = SubscriptionStatus(response=response)
        self.assertEqual(subscription_status.error, None)
        self.assertEqual(subscription_status.subscriptions, ["broadcasts"])

    def test_init_garbage(self):
        response = MockResponse(200, 'abcd')
        subscription_status = SubscriptionStatus(response=response)
        self.assertEqual(subscription_status.error, None)
        self.assertEqual(subscription_status.subscriptions, [])

    def test_str(self):
        response = MockResponse(200, '{"rel":{"topics":{"broadcasts":{"addDate":"2019-02-15"}}}}')
        subscription_status = SubscriptionStatus(response=response)
        self.assertEqual(str(subscription_status), "SubscriptionStatus(subscriptions=['broadcasts'], iid_error=None, error=None)")

    def test_str_error(self):
        response = MockResponse(400, '{"error":"some error"}')
        subscription_status = SubscriptionStatus(response=response)
        self.assertEqual(str(subscription_status), "SubscriptionStatus(subscriptions=[], iid_error=invalid-argument, error=some error)")

    def test_error(self):
        response = MockResponse(400, '{"error":"some error"}')
        subscription_status = SubscriptionStatus(response=response)
        self.assertEqual(subscription_status.error, "some error")
        self.assertEqual(subscription_status.subscriptions, [])
