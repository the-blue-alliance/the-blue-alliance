import json
import unittest2

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from models.account import Account
from models.mobile_client import MobileClient
from models.sitevar import Sitevar

from tbans.consts.subscription_action_type import SubscriptionActionType
from tbans.controllers.subscription_controller import SubscriptionController
from tbans.models.requests.subscriptions.subscription_status_response import SubscriptionStatusResponse

from tests.tbans_tests.mocks.mock_gcm_sitevar import stub_gcm_sitevar


class MockSubscriptionController(SubscriptionController):

    # Despite all logic, it's very hard in Python 2 to make sure we call stub'd methods.
    # So, we're going to return unexpected values from these functions and assert
    # that we got these return values where we expect to get them. This blows.

    @staticmethod
    def _subscribe(user_id, token):
        return "sub"

    @staticmethod
    def _unsubscribe(token):
        return "unsub"


class TestSubscriptionController(unittest2.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_user_stub()
        self.testbed.init_urlfetch_stub(urlmatchers=[(lambda url: True, self._stub_request)])
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        # Default for stubs
        self._mock_response_code = 200
        self._mock_response_content = ''

    def tearDown(self):
        self.testbed.deactivate()

    def _stub_request(self, url, payload, method, headers, request, response, follow_redirects=False, deadline=None, validate_certificate=None, http_proxy=None):
        response.set_statuscode(self._mock_response_code)
        response.set_content(self._mock_response_content)

    def test_update_token_user_id_type(self):
        with self.assertRaises(TypeError):
            SubscriptionController.update_token(1, 'abc')

    def test_update_token_user_id_none(self):
        with self.assertRaises(TypeError):
            SubscriptionController.update_token(None, 'abc')

    def test_update_token_user_id_empty(self):
        with self.assertRaises(ValueError):
            SubscriptionController.update_token('', 'abc')

    def test_update_token_token_type(self):
        with self.assertRaises(TypeError):
            SubscriptionController.update_token('abc', 1)

    def test_update_token_token_none(self):
        with self.assertRaises(TypeError):
            SubscriptionController.update_token('abc', None)

    def test_update_token_token_empty(self):
        with self.assertRaises(ValueError):
            SubscriptionController.update_token('abc', '')

    def test_update_token_subscribe(self):
        user_id = 'abc'
        token = 'def'

        client = MobileClient(
            parent=ndb.Key(Account, user_id),
            user_id=user_id,
            messaging_id=token,
            client_type=1,
            device_uuid='abcdef',
            display_name='Max iPhone 8s').put()

        ret = MockSubscriptionController.update_token(user_id, token)
        self.assertEqual(ret, "sub")

    def test_update_token_unsubscribe(self):
        ret = MockSubscriptionController.update_token('abc', 'abc')
        self.assertEqual(ret, "unsub")

    def test_update_subscriptions_user_id_type(self):
        with self.assertRaises(TypeError):
            SubscriptionController.update_subscriptions(1)

    def test_update_subscriptions_user_id_none(self):
        with self.assertRaises(TypeError):
            SubscriptionController.update_subscriptions(None)

    def test_update_subscriptions_user_id_empty(self):
        with self.assertRaises(ValueError):
            SubscriptionController.update_subscriptions('')

    def test_update_subscriptions(self):
        SubscriptionController.update_subscriptions('abc')

    def test_subscribe(self):
        # Just test code path doesn't crash
        self.stub_gcm_sitevar()
        self._mock_response_content = '{"results": [{}, {}]}'
        self.assertTrue(SubscriptionController._subscribe('abc', 'defg'))

    def test_unsubscribe(self):
        # Just test code path doesn't crash
        self.stub_gcm_sitevar()
        self.assertTrue(SubscriptionController._unsubscribe('abc'))

    def test_update_subscriptions(self):
        user_id = 'abc'

        MobileClient(
            parent=ndb.Key(Account, user_id),
            user_id=user_id,
            messaging_id='defg',
            client_type=1,
            device_uuid='abcdef',
            display_name='Max iPhone 8s').put()

        self.stub_gcm_sitevar()
        self._mock_response_content = '{"results": [{}]}'
        self.assertTrue(SubscriptionController.update_subscriptions(user_id))

    def test_make_batch_requests(self):
        self.stub_gcm_sitevar()
        self._mock_response_content = '{"results": [{}, {}]}'
        self.assertTrue(SubscriptionController._make_batch_requests(['abc', 'def'], ['topic_one'], SubscriptionActionType.ADD))

    def test_make_batch_requests_error(self):
        self.stub_gcm_sitevar()
        self._mock_response_content = '{"error": "some error"}'
        self.assertFalse(SubscriptionController._make_batch_requests(['abc', 'def'], ['topic_one'], SubscriptionActionType.ADD))

    def test_make_batch_requests_partial_error_no_delete(self):
        user_id = 'abc'

        MobileClient(
            parent=ndb.Key(Account, user_id),
            user_id=user_id,
            messaging_id='abc',
            client_type=1,
            device_uuid='abcdef',
            display_name='Max iPhone 8s').put()
        MobileClient(
            parent=ndb.Key(Account, user_id),
            user_id=user_id,
            messaging_id='defg',
            client_type=1,
            device_uuid='abcdef',
            display_name='Max iPhone 8s').put()
        # Sanity check
        self.assertEqual(len(MobileClient.query().fetch()), 2)

        self.stub_gcm_sitevar()
        self._mock_response_content = '{"results": [{}, {"error":"TOO_MANY_TOPICS"}]}'
        self.assertFalse(SubscriptionController._make_batch_requests(['abc', 'defg'], ['topic_one'], SubscriptionActionType.ADD))
        self.assertEqual(len(MobileClient.query().fetch()), 2)

    def test_make_batch_requests_partial_error_delete(self):
        user_id = 'abc'

        MobileClient(
            parent=ndb.Key(Account, user_id),
            user_id=user_id,
            messaging_id='abc',
            client_type=1,
            device_uuid='abcdef',
            display_name='Max iPhone 8s').put()
        MobileClient(
            parent=ndb.Key(Account, user_id),
            user_id=user_id,
            messaging_id='defg',
            client_type=1,
            device_uuid='abcdef',
            display_name='Max iPhone 8s').put()
        # Sanity check
        self.assertEqual(len(MobileClient.query().fetch()), 2)

        self.stub_gcm_sitevar()
        self._mock_response_content = '{"results": [{}, {"error":"INVALID_ARGUMENT"}]}'
        self.assertTrue(SubscriptionController._make_batch_requests(['abc', 'defg'], ['topic_one'], SubscriptionActionType.ADD))
        self.assertEqual(len(MobileClient.query().fetch()), 1)

    def test_make_status_request(self):
        self.stub_gcm_sitevar()
        self.assertIsNotNone(SubscriptionController._make_status_request('abc'))

    def test_make_status_request_error(self):
        self.stub_gcm_sitevar()
        self._mock_response_code = 500
        self._mock_response_content = '{"error": "some error"}'
        self.assertIsNone(SubscriptionController._make_status_request('abc'))

    def test_make_status_request_invalid_argument_error(self):
        user_id = 'abc'
        token = 'some-token'

        self.stub_gcm_sitevar()
        MobileClient(
            parent=ndb.Key(Account, user_id),
            user_id=user_id,
            messaging_id=token,
            client_type=1,
            device_uuid='abcdef',
            display_name='Max iPhone 8s').put()
        # Sanity check
        self.assertEqual(len(MobileClient.query().fetch()), 1)

        self._mock_response_code = 400
        self._mock_response_content = '{"error": "some error"}'
        self.assertIsNotNone(SubscriptionController._make_status_request(token))
        self.assertEqual(len(MobileClient.query().fetch()), 0)

    def test_fcm_api_key_no_sitevar(self):
        with self.assertRaises(Exception):
            SubscriptionController._fcm_api_key()

    def test_fcm_api_key_no_key(self):
        gcm_sitevar = Sitevar(
            id='gcm.serverKey'
        )
        gcm_sitevar.put()

        with self.assertRaises(Exception):
            SubscriptionController._fcm_api_key()

    def test_fcm_api_key(self):
        self.stub_gcm_sitevar()
        self.assertEqual(SubscriptionController._fcm_api_key(), 'abcd')
