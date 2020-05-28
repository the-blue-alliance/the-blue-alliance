import json
import unittest2
import webapp2
import webtest

from google.appengine.ext import testbed

from controllers.api.api_base_controller import ApiBaseController


class TestTeamApi(unittest2.TestCase):
    def setUp(self):
        app = webapp2.WSGIApplication([webapp2.Route(r'/', ApiBaseController, methods=['GET'])], debug=True)
        self.testapp = webtest.TestApp(app)

        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_urlfetch_stub()

    def tearDown(self):
        self.testbed.deactivate()

    def test_validate_app_id(self):
        response = self.testapp.get('/', expect_errors=True)  # By default get() doesn't send a X-TBA-App-ID
        self.assertEqual(response.status, "400 Bad Request")
        self.assertTrue('Error' in json.loads(response.body).keys())

        response = self.testapp.get('/', headers={"X-TBA-App-Id": "this:is:a:bad:id"}, expect_errors=True)
        self.assertEqual(response.status, "400 Bad Request")
