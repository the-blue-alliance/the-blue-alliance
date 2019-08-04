import unittest2

from tests.tbans_tests.mocks.mock_tbans_service import MockTBANSService

from helpers.tbans_helper import TBANSHelper
from tba.models.mobile_client import MobileClient
from tba.consts.client_type import ClientType


# These are mostly setup to test that code paths don't crash when calling
# Note: We don't test any values that get sent to the API - this isn't great
# but also doing this sort of mocking is really hard without python3/mock
class TestTBANSHelper(unittest2.TestCase):

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

    def test_update_favorites(self):
        TBANSHelper._create_service = self._create_mock_service
        TBANSHelper.update_favorites(user_id='abc')
        TBANSHelper.update_favorites(user_id='abc', sending_device_key='def')

    def test_update_subscriptions(self):
        TBANSHelper._create_service = self._create_mock_service
        TBANSHelper.update_subscriptions(user_id='abc')
        TBANSHelper.update_subscriptions(user_id='abc', sending_device_key='def')

    def test_ping_webhook(self):
        TBANSHelper._create_service = self._create_mock_service
        client = MobileClient(client_type=ClientType.WEBHOOK)
        TBANSHelper.ping_webhook(client)

    def test_ping_webhook(self):
        TBANSHelper._create_service = self._create_mock_service
        TBANSHelper.verify_webhook(url='abc', secret='def')

    def _create_mock_service(self):
        return MockTBANSService()
