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

        self.service = TBANSService(testing=True)

    def _stub_request(self, url, payload, method, headers, request, response, follow_redirects=False, deadline=None, validate_certificate=None, http_proxy=None):
        response.set_statuscode(self._response_status_code)
        response.set_content(getattr(self, '_response_content', None))

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
        self._response_status_code = 200
        self._response_content = '{"name": "projects/{project_id}/messages/1545762214218984"}'
        request = PingRequest(fcm=FCM(token='abc'))
        response = self.service.ping(request)
        self.assertEqual(response.code, self._response_status_code)
        self.assertEqual(response.message, self._response_content)

    def test_ping_webhook(self):
        self._response_status_code = 200
        request = PingRequest(webhook=Webhook(url='https://www.thebluealliance.com', secret='password'))
        response = self.service.ping(request)
        self.assertEqual(response.code, 200)
        self.assertEqual(response.message, None)

    def test_verification(self):
        self._response_status_code = 200
        request = VerificationRequest(webhook=Webhook(url='https://www.thebluealliance.com', secret='password'))
        response = self.service.verification(request)
        self.assertTrue(isinstance(response, VerificationResponse))
        self.assertEqual(response.code, 200)
        self.assertEqual(response.message, None)
