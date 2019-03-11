# test_tbans_subscription_status_request.py

import unittest2
import uuid

from google.appengine.ext import testbed

from tbans.models.subscriptions.subscription_status import SubscriptionStatus
from tbans.models.subscriptions.subscription_status_request import SubscriptionStatusRequest

from tests.tbans_tests.mocks.mock_response import MockResponse


class TestSubscriptionStatusRequest(unittest2.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_app_identity_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_urlfetch_stub(urlmatchers=[(lambda url: True, self._stub_iid_request)])

        # Generate a random token to use each test
        self.token = str(uuid.uuid4())

    def tearDown(self):
        self.testbed.deactivate()

    def _stub_iid_request(self, url, payload, method, headers, request, response, follow_redirects=False, deadline=None, validate_certificate=None, http_proxy=None):
        # While we're here - check that our request looks right
        self.assertEqual(url, 'https://iid.googleapis.com/iid/info/{}?details=true'.format(self.token))

        # We need to make sure that we have an Auth header, but we don't care what it is
        headers = {header.key(): header.value() for header in headers}
        authorization_header = headers.get('Authorization', None)
        self.assertIsNotNone(authorization_header)

        self.assertIsNone(payload)
        self.assertEqual(method, 'GET')
        response.set_statuscode(200)
        response.set_content('{"rel":{"topics":{"broadcasts":{"addDate":"2019-02-15"}}},"platform":"IOS"}')

    def test_init_token_none(self):
        with self.assertRaises(TypeError):
            SubscriptionStatusRequest()

    def test_init_token_type(self):
        with self.assertRaises(ValueError):
            SubscriptionStatusRequest(token=1)

    def test_str(self):
        request = SubscriptionStatusRequest(token=self.token)
        self.assertEqual(str(request), 'SubscriptionStatusRequest(token={})'.format(self.token))

    def test_iid_info_url(self):
        request = SubscriptionStatusRequest(token=self.token)
        self.assertEqual(request._iid_info_url, 'https://iid.googleapis.com/iid/info/{}?details=true'.format(self.token))

    def test_send(self):
        request = SubscriptionStatusRequest(token=self.token)
        response = request.send()
        self.assertEqual(response.subscriptions, ['broadcasts'])
        self.assertIsNone(response.error)
