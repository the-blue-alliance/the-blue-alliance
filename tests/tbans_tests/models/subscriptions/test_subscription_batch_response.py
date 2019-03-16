import unittest2

from tbans.models.subscriptions.subscription_batch_response import SubscriptionBatchResponse

from tests.tbans_tests.mocks.mock_response import MockResponse


class TestSubscriptionBatchResponse(unittest2.TestCase):

    def test_tokens_type(self):
        with self.assertRaises(ValueError):
            SubscriptionBatchResponse(tokens=1)

    def test_tokens_empty(self):
        with self.assertRaises(ValueError):
            SubscriptionBatchResponse(tokens=[])

    def test_tokens_mixed(self):
        with self.assertRaises(ValueError):
            SubscriptionBatchResponse(tokens=['abc', 1])

    def test_result_none(self):
        with self.assertRaises(ValueError):
            SubscriptionBatchResponse(tokens=['abc'], response=None)

    def test_result_type(self):
        response = MockResponse(200, '{"results": []}')
        with self.assertRaises(ValueError):
            SubscriptionBatchResponse(tokens=['abc'], response=response)

    def test_result_type_error(self):
        # init with an empty results but with an error is valid
        response = MockResponse(400, '{"error": "some error"}')
        batch_response = SubscriptionBatchResponse(tokens=['abc'], response=response)
        self.assertEqual(batch_response.error, "some error")
        self.assertEqual(batch_response.subscribers, [])

    def test_init(self):
        response = MockResponse(200, '{"results": [{}]}')
        batch_response = SubscriptionBatchResponse(tokens=['abc'], response=response)
        self.assertEqual(len(batch_response.subscribers), 1)
        subscriber = batch_response.subscribers[0]
        self.assertEqual(subscriber.token, 'abc')
