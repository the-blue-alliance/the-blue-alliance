import json
import unittest2
import webapp2
import webtest

from google.appengine.api import taskqueue
from google.appengine.ext import ndb
from google.appengine.ext import testbed

from models.account import Account
from models.mobile_client import MobileClient

from tbans.workers.subscription_worker import SubscriptionWorkerHandler

from tests.tbans_tests.mocks.mock_gcm_sitevar import stub_gcm_sitevar


class TestSubscriptionWorker(unittest2.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_user_stub()
        self.testbed.init_urlfetch_stub(urlmatchers=[(lambda url: True, self._stub_request)])
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        self.testbed.init_taskqueue_stub(root_path='.')
        self.taskqueue_stub = self.testbed.get_stub(testbed.TASKQUEUE_SERVICE_NAME)

        app = webapp2.WSGIApplication([('/', SubscriptionWorkerHandler)])
        self.testapp = webtest.TestApp(app)

    def tearDown(self):
        self.testbed.deactivate()

    def _stub_request(self, url, payload, method, headers, request, response, follow_redirects=False, deadline=None, validate_certificate=None, http_proxy=None):
        response.set_statuscode(500)
        response.set_content('{"error": "Some error here"}')

    def test_task_queue(self):
        queue = SubscriptionWorkerHandler.task_queue()
        self.assertEqual(queue.name, 'tbans-update-subscriptions')

    def test_handler_get(self):
        with self.assertRaises(Exception):
            self.testapp.get('/')

    def test_drains_queue(self):
        user_id = 'abcd'
        # Add several tasks
        json_payload = json.dumps({'user_id': user_id})
        pull_queue = SubscriptionWorkerHandler.task_queue()
        for i in xrange(4):
            pull_queue.add(taskqueue.Task(payload=json_payload, method='PULL', tag=user_id))

        # Assert tasks
        pull_tasks_before = self.taskqueue_stub.get_filtered_tasks(queue_names=['tbans-update-subscriptions'])
        self.assertEqual(len(pull_tasks_before), 4)

        response = self.testapp.post('/', {'tag': user_id})
        self.assertEqual(response.status_int, 200)

        pull_tasks_after = self.taskqueue_stub.get_filtered_tasks(queue_names=['tbans-update-subscriptions'])
        self.assertEqual(len(pull_tasks_after), 0)

    def test_drains_queue_fail(self):
        stub_gcm_sitevar()

        user_id = 'abcd'
        # Add several tasks
        json_payload = json.dumps({'user_id': user_id})
        pull_queue = SubscriptionWorkerHandler.task_queue()
        for i in xrange(4):
            pull_queue.add(taskqueue.Task(payload=json_payload, method='PULL', tag=user_id))

        # Setup a dummy client to hit our code path
        client = MobileClient(
            parent=ndb.Key(Account, user_id),
            user_id=user_id,
            messaging_id='some token',
            client_type=1,
            device_uuid='abcdef',
            display_name='Max iPhone 8s').put()

        # Assert tasks
        pull_tasks_before = self.taskqueue_stub.get_filtered_tasks(queue_names=['tbans-update-subscriptions'])
        self.assertEqual(len(pull_tasks_before), 4)

        try:
            response = self.testapp.post('/', {'tag': user_id})
            self.assertEqual(response.status_int, 500)
        except:
            pass

        pull_tasks_after = self.taskqueue_stub.get_filtered_tasks(queue_names=['tbans-update-subscriptions'])
        self.assertEqual(len(pull_tasks_after), 1)
