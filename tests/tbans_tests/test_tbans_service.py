from firebase_admin import messaging
import unittest2

from protorpc import remote

from google.appengine.api import taskqueue
from google.appengine.ext import testbed

from tbans.models.service.messages import FCM, Webhook, PingRequest, \
    UpdateMyTBARequest, VerificationRequest, VerificationResponse
from tbans.tbans_service import TBANSService


class TestTBANSService(unittest2.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_app_identity_stub()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_urlfetch_stub(urlmatchers=[(lambda url: True, self._stub_request)])
        # Stub the FCM admin module
        messaging.send_multicast = self._stub_send_multicast

        self.testbed.init_taskqueue_stub(root_path='.')
        self.taskqueue_stub = self.testbed.get_stub(testbed.TASKQUEUE_SERVICE_NAME)

        self.service = TBANSService()

    def _stub_send_multicast(message, dry_run, app):
        pass

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
        self.assertEqual(response.message, None)

    def test_ping_webhook(self):
        request = PingRequest(webhook=Webhook(url='https://www.thebluealliance.com', secret='password'))
        response = self.service.ping(request)
        self.assertEqual(response.code, 200)
        self.assertEqual(response.message, None)

    def test_update_favorites(self):
        request = UpdateMyTBARequest(user_id='abc')
        response = self.service.update_favorites(request)
        self.assertEqual(response.code, 200)
        self.assertEqual(response.message, None)

        push_tasks = self.taskqueue_stub.get_filtered_tasks(queue_names=['tbans-notifications'])
        self.assertEqual(len(push_tasks), 1)

        push_task = push_tasks[0]
        self.assertEqual(push_task.extract_params(), {'notification_type': '100', 'user_id': 'abc', 'vertical_type': '0'})

    def test_update_favorites_sending_device_key(self):
        request = UpdateMyTBARequest(user_id='abc', sending_device_key='defg')
        response = self.service.update_favorites(request)
        self.assertEqual(response.code, 200)
        self.assertEqual(response.message, None)

        push_tasks = self.taskqueue_stub.get_filtered_tasks(queue_names=['tbans-notifications'])
        self.assertEqual(len(push_tasks), 1)

        push_task = push_tasks[0]
        self.assertEqual(push_task.extract_params(), {'notification_type': '100', 'sending_device_key': 'defg', 'user_id': 'abc', 'vertical_type': '0'})

    def test_update_subscriptions(self):
        request = UpdateMyTBARequest(user_id='abc')
        response = self.service.update_subscriptions(request)
        self.assertEqual(response.code, 200)
        self.assertEqual(response.message, None)

        push_tasks = self.taskqueue_stub.get_filtered_tasks(queue_names=['tbans-notifications'])
        self.assertEqual(len(push_tasks), 1)

        push_task = push_tasks[0]
        self.assertEqual(push_task.extract_params(), {'notification_type': '101', 'user_id': 'abc', 'vertical_type': '0'})

    def test_update_subscriptions_sending_device_key(self):
        request = UpdateMyTBARequest(user_id='abc', sending_device_key='defg')
        response = self.service.update_subscriptions(request)
        self.assertEqual(response.code, 200)
        self.assertEqual(response.message, None)

        push_tasks = self.taskqueue_stub.get_filtered_tasks(queue_names=['tbans-notifications'])
        self.assertEqual(len(push_tasks), 1)

        push_task = push_tasks[0]
        self.assertEqual(push_task.extract_params(), {'notification_type': '101', 'sending_device_key': 'defg', 'user_id': 'abc', 'vertical_type': '0'})

    def test_verification(self):
        request = VerificationRequest(webhook=Webhook(url='https://www.thebluealliance.com', secret='password'))
        response = self.service.verification(request)
        self.assertTrue(isinstance(response, VerificationResponse))
        self.assertEqual(response.code, 200)
        self.assertEqual(response.message, None)
        self.assertIsNotNone(response.verification_key)
