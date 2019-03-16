import unittest2

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from tests.tbans_tests.mocks.mock_tbans_service import MockTBANSService

from consts.client_type import ClientType
from models.account import Account
from models.mobile_client import MobileClient
from helpers.tbans_helper import TBANSHelper


# These are mostly setup to test that code paths don't crash when calling
# Note: We don't test any values that get sent to the API - this isn't great
# but also doing this sort of mocking is really hard without python3/mock
class TestTBANSHelper(unittest2.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

    def tearDown(self):
        self.testbed.deactivate()

    def test_create_service(self):
        service = TBANSHelper._create_service()
        self.assertIsNotNone(service)

    def test_ping_ping_client(self):
        TBANSHelper._create_service = self._create_mock_service
        client = MobileClient(client_type=ClientType.OS_IOS)
        TBANSHelper.ping(client)

    def test_ping_ping_webhook(self):
        TBANSHelper._create_service = self._create_mock_service
        client = MobileClient(client_type=ClientType.WEBHOOK)
        TBANSHelper.ping(client)

    def test_ping_client(self):
        TBANSHelper._create_service = self._create_mock_service
        client = MobileClient(client_type=ClientType.OS_IOS)
        TBANSHelper.ping_client(client)

    def test_ping_webhook(self):
        TBANSHelper._create_service = self._create_mock_service
        client = MobileClient(client_type=ClientType.WEBHOOK)
        TBANSHelper.ping_webhook(client)

    def test_update_client_invalid(self):
        client = self._create_client(ClientType.WEBHOOK)
        TBANSHelper._create_service = self._create_mock_service
        TBANSHelper.update_client(client=client)

    def test_update_client(self):
        client = self._create_client(ClientType.OS_IOS)
        TBANSHelper._create_service = self._create_mock_service
        TBANSHelper.update_client(client=client)

    def test_update_subscriptions(self):
        TBANSHelper._create_service = self._create_mock_service
        TBANSHelper.update_subscriptions(user_id='abc')

    def test_verify_webhook(self):
        TBANSHelper._create_service = self._create_mock_service
        TBANSHelper.verify_webhook(url='abc', secret='def')

    def _create_mock_service(self):
        return MockTBANSService()

    def _create_client(self, client_type):
        user_id = 'abc'
        return MobileClient(
            parent=ndb.Key(Account, user_id),
            user_id=user_id,
            messaging_id='abcdef',
            client_type=client_type,
            device_uuid='test-test-test',
            display_name='test')
