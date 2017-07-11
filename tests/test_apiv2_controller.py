import unittest2
import webtest
import webapp2

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from controllers.api.api_event_controller import ApiEventController


class TestApiController(unittest2.TestCase):
    def setUp(self):
        # Use ApiEventController as a random API controller to test on
        app = webapp2.WSGIApplication([webapp2.Route(r'/<event_key:>', ApiEventController, methods=['GET'])], debug=True)
        self.testapp = webtest.TestApp(app)

        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_urlfetch_stub()
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        self.testbed.init_taskqueue_stub(root_path=".")

    def tearDown(self):
        self.testbed.deactivate()

    def test_validate_tba_app_id(self):
        # Fail
        response = self.testapp.get('/2010sc', expect_errors=True)
        self.assertEqual(response.status_code, 400)
        self.assertTrue('Error' in response.json)

        # Fail
        response = self.testapp.get('/2010sc', headers={'X-TBA-App-Id': ''}, expect_errors=True)
        self.assertEqual(response.status_code, 400)
        self.assertTrue('Error' in response.json)

        # Fail
        response = self.testapp.get('/2010sc', headers={'X-TBA-App-Id': '::'}, expect_errors=True)
        self.assertEqual(response.status_code, 400)
        self.assertTrue('Error' in response.json)

        # Fail
        response = self.testapp.get('/2010sc', headers={'X-TBA-App-Id': 'a::'}, expect_errors=True)
        self.assertEqual(response.status_code, 400)
        self.assertTrue('Error' in response.json)

        # Fail
        response = self.testapp.get('/2010sc', headers={'X-TBA-App-Id': 'a:a:'}, expect_errors=True)
        self.assertEqual(response.status_code, 400)
        self.assertTrue('Error' in response.json)

        # Pass, event not in database
        response = self.testapp.get('/2010sc', headers={'X-TBA-App-Id': 'a:a:a'}, expect_errors=True)
        self.assertEqual(response.status_code, 404)
        self.assertTrue('404' in response.json)
