import unittest2
import webapp2
import webtest

from controllers.slack_controller import SlackHandler, ModQueueHandler

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from sitevars.slack_commands import SlackCommands


class MockSlackHandler(SlackHandler):

    def get(self):
        verify_command = self.request.get('verify_command', None)
        if verify_command:
            self.verify_command(verify_command)

        require_user = self.request.get('require_user', None)
        if require_user:
            self.require_user(require_user)

        require_channel = self.request.get('require_channel', None)
        if require_channel:
            self.require_channel(require_channel)

    def handle_exception(self, exception, debug):
        self.response.write(str(exception))

        # If the exception is a HTTPException, use its error code.
        # Otherwise use a generic 500 error code.
        if isinstance(exception, webapp2.HTTPException):
            self.response.set_status(exception.code)
        else:
            self.response.set_status(500)


class TestSlackHandler(unittest2.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_user_stub()
        self.testbed.init_urlfetch_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        app = webapp2.WSGIApplication([
            ('/test', MockSlackHandler),
        ])
        self.testapp = webtest.TestApp(app)

    def tearDown(self):
        self.testbed.deactivate()

    def test_require_command_no_command(self):
        response = self.testapp.get('/test', {'verify_command': '/test'}, expect_errors=True)
        self.assertTrue('Command required to be /test' in response.body)
        self.assertEqual(response.status_code, 500)

    def test_require_command_no_token(self):
        response = self.testapp.get('/test', {'verify_command': '/test', 'command': '/test'}, expect_errors=True)
        self.assertTrue('No token for command /test' in response.body)
        self.assertEqual(response.status_code, 500)

    def test_require_command_token_not_equal(self):
        SlackCommands.set_token('/test', 'abcd')
        response = self.testapp.get('/test', {'verify_command': '/test', 'command': '/test', 'token': 'efgh'}, expect_errors=True)
        self.assertTrue('Tokens do not match for command: /test' in response.body)
        self.assertEqual(response.status_code, 500)

    def test_require_command(self):
        SlackCommands.set_token('/test', 'abcd')
        response = self.testapp.get('/test', {'verify_command': '/test', 'command': '/test', 'token': 'abcd'})
        self.assertEqual(response.status_code, 200)

    def test_require_user_false(self):
        response = self.testapp.get('/test', {'require_user': 'user', 'user_name': 'notuser'}, expect_errors=True)
        self.assertTrue('Command required to be run by user' in response.body)
        self.assertEqual(response.status_code, 500)

    def test_require_user(self):
        response = self.testapp.get('/test', {'require_user': 'user', 'user_name': 'user'})
        self.assertEqual(response.status_code, 200)

    def test_require_channel_false(self):
        response = self.testapp.get('/test', {'require_channel': 'channel', 'channel_name': 'notchannel'}, expect_errors=True)
        self.assertTrue('Command required to be run in #channel' in response.body)
        self.assertEqual(response.status_code, 500)

    def test_require_channel(self):
        response = self.testapp.get('/test', {'require_channel': 'channel', 'channel_name': 'channel'})
        self.assertEqual(response.status_code, 200)


class MockModQueueHandler(ModQueueHandler):

    def handle_exception(self, exception, debug):
        self.response.write(str(exception))

        # If the exception is a HTTPException, use its error code.
        # Otherwise use a generic 500 error code.
        if isinstance(exception, webapp2.HTTPException):
            self.response.set_status(exception.code)
        else:
            self.response.set_status(500)


class TestModQueue(unittest2.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_user_stub()
        self.testbed.init_urlfetch_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        SlackCommands.set_token('/modqueue', 'abcd')
        app = webapp2.WSGIApplication([
            ('/modqueue', MockModQueueHandler),
        ])
        self.testapp = webtest.TestApp(app)

    def tearDown(self):
        self.testbed.deactivate()

    def test_modqueue_command(self):
        response = self.testapp.get('/modqueue', {'channel_name': 'mods', 'token': 'defg'}, expect_errors=True)
        self.assertTrue('Command required to be /modqueue' in response.body)
        self.assertEqual(response.status_code, 500)

    def test_modqueue_token(self):
        response = self.testapp.get('/modqueue', {'channel_name': 'mods', 'token': 'defg', 'command': '/modqueue'}, expect_errors=True)
        print(response.body)
        self.assertTrue('Tokens do not match for command: /modqueue' in response.body)
        self.assertEqual(response.status_code, 500)

    def test_modqueue_channel(self):
        response = self.testapp.get('/modqueue', {'channel_name': 'notmods', 'token': 'abcd', 'command': '/modqueue'}, expect_errors=True)
        self.assertTrue('Command required to be run in #mods' in response.body)
        self.assertEqual(response.status_code, 500)

    def test_modqueue(self):
        response = self.testapp.get('/modqueue', {'command': '/modqueue', 'token': 'abcd', 'channel_name': 'mods'})
        self.assertEqual(response.status_code, 200)
