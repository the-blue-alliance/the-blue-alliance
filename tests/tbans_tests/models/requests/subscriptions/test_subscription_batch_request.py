import unittest2

from google.appengine.ext import testbed

from tbans.consts.subscription_action_type import SubscriptionActionType
from tbans.models.requests.subscriptions.subscription_batch_request import SubscriptionBatchRequest
from tbans.models.requests.subscriptions.subscription_batch_response import SubscriptionBatchResponse


class TestSubscriptionBatchRequest(unittest2.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_app_identity_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_urlfetch_stub(urlmatchers=[(lambda url: True, self._stub_iid_batch_request)])

    def tearDown(self):
        self.testbed.deactivate()

    def _stub_iid_batch_request(self, url, payload, method, headers, request, response, follow_redirects=False, deadline=None, validate_certificate=None, http_proxy=None):
        # While we're here - check that our request looks right
        self.assertTrue(url.startswith('https://iid.googleapis.com/iid/'))

        # We need to make sure that we have an Auth header, but we don't care what it is
        headers = {header.key(): header.value() for header in headers}
        authorization_header = headers.get('Authorization', None)
        self.assertIsNotNone(authorization_header)

        self.assertEqual(payload, '{"to": "/topics/broadcasts", "registration_tokens": ["abc"]}')
        self.assertEqual(method, 'POST')
        response.set_statuscode(200)
        response.set_content('{"results":[{}]}')

    def test_tokens(self):
        request = SubscriptionBatchRequest('abc', 'broadcasts', SubscriptionActionType.ADD)
        self.assertEqual(request.tokens, ['abc'])

    def test_tokens_empty(self):
        with self.assertRaises(ValueError):
            SubscriptionBatchRequest([], 'broadcasts', SubscriptionActionType.ADD)

    def test_tokens_type(self):
        with self.assertRaises(TypeError):
            SubscriptionBatchRequest(2, 'broadcasts', SubscriptionActionType.ADD)

    def test_token_value_none(self):
        with self.assertRaises(TypeError):
            SubscriptionBatchRequest(None, 'broadcasts', SubscriptionActionType.ADD)

    def test_tokens_type(self):
        with self.assertRaises(ValueError):
            SubscriptionBatchRequest([], 'broadcasts', SubscriptionActionType.ADD)

    def test_token_value(self):
        with self.assertRaises(ValueError):
            SubscriptionBatchRequest([2], 'broadcasts', SubscriptionActionType.ADD)

    def test_token_value_mixed(self):
        with self.assertRaises(ValueError):
            SubscriptionBatchRequest(['abc', 2], 'broadcasts', SubscriptionActionType.ADD)

    def test_token_value_len(self):
        max = 1000
        with self.assertRaises(ValueError):
            SubscriptionBatchRequest(['abc' for _ in xrange(max + 1)], 'broadcasts', SubscriptionActionType.ADD)
        SubscriptionBatchRequest(['abc' for _ in xrange(max)], 'broadcasts', SubscriptionActionType.ADD)

    def test_topic_fixed(self):
        request = SubscriptionBatchRequest('abc', 'broadcasts', SubscriptionActionType.ADD)
        self.assertEqual(request.topic, '/topics/broadcasts')

    def test_topic(self):
        request = SubscriptionBatchRequest('abc', '/topics/broadcasts', SubscriptionActionType.ADD)
        self.assertEqual(request.topic, '/topics/broadcasts')

    def test_topic_type(self):
        with self.assertRaises(TypeError):
            SubscriptionBatchRequest('abc', 1, SubscriptionActionType.ADD)

    def test_topic_none(self):
        with self.assertRaises(TypeError):
            SubscriptionBatchRequest('abc', None, SubscriptionActionType.ADD)

    def test_topic_empty(self):
        with self.assertRaises(ValueError):
            SubscriptionBatchRequest('abc', '', SubscriptionActionType.ADD)

    def test_action_type(self):
        SubscriptionBatchRequest('abc', 'broadcasts', SubscriptionActionType.ADD)

    def test_action_type(self):
        with self.assertRaises(ValueError):
            SubscriptionBatchRequest('abc', 'broadcasts', -1)

    def test_str(self):
        request = SubscriptionBatchRequest('abc', 'broadcasts', SubscriptionActionType.REMOVE)
        self.assertEqual(str(request), "SubscriptionBatchRequest(tokens=['abc'], topic=/topics/broadcasts, method=v1:batchRemove)")

    def test_iid_info_url(self):
        for action_type in SubscriptionActionType.batch_actions:
            method = SubscriptionActionType.BATCH_METHODS[action_type]
            request = SubscriptionBatchRequest('abc', 'broadcasts', action_type)
            self.assertEqual(request._batch_url, 'https://iid.googleapis.com/iid/{}'.format(method))

    def test_send(self):
        request = SubscriptionBatchRequest('abc', 'broadcasts', SubscriptionActionType.REMOVE)
        response = request.send()
        self.assertIsNotNone(response.subscribers)
        self.assertEqual(len(response.subscribers), 1)
        self.assertIsNone(response.error)
