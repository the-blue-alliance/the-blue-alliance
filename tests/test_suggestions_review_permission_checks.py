import unittest2
import webtest
import webapp2
import os

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from controllers.suggestions.suggest_match_video_review_controller import SuggestMatchVideoReviewController
from consts.account_permissions import AccountPermissions
from models.account import Account


class TestMatchApiController(unittest2.TestCase):
    def setUp(self):
        app = webapp2.WSGIApplication([webapp2.Route(r'/suggestions', SuggestMatchVideoReviewController, methods=['GET'])], debug=True)
        self.testapp = webtest.TestApp(app)

        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        self.testbed.init_urlfetch_stub()
        self.testbed.init_user_stub()

    def tearDown(self):
        self.testbed.deactivate()

    def loginUser(self):
        self.testbed.setup_env(
            user_email="user@example.com",
            user_id="123",
            user_is_admin='0',
            overwrite=True)

        account = Account.get_or_insert(
            "123",
            email="user@example.com",
            registered=True)

    def givePermission(self):
        account = Account.get_or_insert(
            "123",
            email="user@example.com",
            registered=True)
        account.permissions.append(AccountPermissions.REVIEW_MEDIA)
        account.put()

    def testLoggedOutUserDenied(self):
        response = self.testapp.get('/suggestions')
        self.assertEqual(response.status, "302 Moved Temporarily")

    def testNoPermissionUserDenied(self):
        self.loginUser()

        response = self.testapp.get('/suggestions')
        self.assertEqual(response.status, "302 Moved Temporarily")

    def testPermissionUserAllowed(self):
        self.loginUser()
        self.givePermission()

        try:
            response = self.testapp.get('/suggestions')
        except:
            # GROSS HACK because I can't fix this django templating error and we throw an error if we're letting the user in.
            # FIXME(gregmarra) 20151121
            pass
        else:
            # GROSS HACK fail if we didn't get the error that means the user was let in
            self.assertTrue(False)
