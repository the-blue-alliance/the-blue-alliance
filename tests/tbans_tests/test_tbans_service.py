from firebase_admin import messaging
import unittest2

from protorpc import remote

from google.appengine.ext import testbed

from tbans.models.service.messages import FCM, Webhook, PingRequest, VerificationRequest, VerificationResponse
from tbans.tbans_service import TBANSService


class TestTBANSService(unittest2.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_app_identity_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_urlfetch_stub(urlmatchers=[(lambda url: True, self._stub_request)])
        # Stub the FCM admin module
        messaging.send = self._stub_send

        self.service = TBANSService()

    def _stub_send(message, dry_run, app):
        return 'message-id'

    def _stub_request(self, url, payload, method, headers, request, response, follow_redirects=False, deadline=None, validate_certificate=None, http_proxy=None):
        pass

    def test_init_fcm(self):
        self.assertIsNotNone(self.service._firebase_app)
        firebase_app = self.service._firebase_app
        self.assertEqual(firebase_app.name, 'tbans')
        self.assertIsNotNone(firebase_app.credential)
        self.assertEqual(firebase_app.project_id, 'testbed-test')

    def test_ping_no_delivery(self):
        request = PingRequest()
        response = self.service.ping(request)
        self.assertEqual(response.code, 400)
        self.assertEqual(response.message, 'Did not specify FCM or webhook to ping')

    def test_ping_both_delivery(self):
        request = PingRequest(fcm=FCM(token='abc'), webhook=Webhook(url='https://www.thebluealliance.com', secret='password'))
        response = self.service.ping(request)
        self.assertEqual(response.code, 400)
        self.assertEqual(response.message, 'Cannot ping both FCM and webhook')

    def test_ping_fcm(self):
        request = PingRequest(fcm=FCM(token='abc'))
        response = self.service.ping(request)
        self.assertEqual(response.code, 200)
        self.assertEqual(response.message, 'message-id')

    def test_ping_webhook(self):
        request = PingRequest(webhook=Webhook(url='https://www.thebluealliance.com', secret='password'))
        response = self.service.ping(request)
        self.assertEqual(response.code, 200)
        self.assertEqual(response.message, None)

    def test_verification(self):
        request = VerificationRequest(webhook=Webhook(url='https://www.thebluealliance.com', secret='password'))
        response = self.service.verification(request)
        self.assertTrue(isinstance(response, VerificationResponse))
        self.assertEqual(response.code, 200)
        self.assertEqual(response.message, None)
        self.assertIsNotNone(response.verification_key)
