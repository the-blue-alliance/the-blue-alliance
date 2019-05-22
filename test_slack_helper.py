import unittest2

from helpers.slack_helper import SlackHelper

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from sitevars.slack_commands import SlackCommands


class TestSlackHelper(unittest2.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_user_stub()
        self.testbed.init_urlfetch_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

    def tearDown(self):
        self.testbed.deactivate()

    def test_require_command_no_command(self):
        request_body = {'command': None}
        with self.assertRaises(Exception) as context:
            SlackHelper.verify_command(request_body, '/test')
        self.assertTrue('Command required to be /test' in context.exception)

    def test_require_command_no_token(self):
        request_body = {'command': '/test'}
        with self.assertRaises(Exception) as context:
            SlackHelper.verify_command(request_body, '/test')
        self.assertTrue('No token for command /test' in context.exception)

    def test_require_command_no_token_request(self):
        SlackCommands.set_token('/test', 'abcd')
        request_body = {'command': '/test', 'token': None}
        with self.assertRaises(Exception) as context:
            SlackHelper.verify_command(request_body, '/test')
        self.assertTrue('No token from request for command /test' in context.exception)

    def test_require_command_not_equal(self):
        SlackCommands.set_token('/test', 'abcd')
        request_body = {'command': '/test', 'token': 'abcdefg'}
        with self.assertRaises(Exception) as context:
            SlackHelper.verify_command(request_body, '/test')
        self.assertTrue('Tokens do not match for command: /test' in context.exception)

    def test_require_command(self):
        SlackCommands.set_token('/test', 'abcd')
        request_body = {'command': '/test', 'token': 'abcd'}
        SlackHelper.verify_command(request_body, '/test')

    def test_require_user_false(self):
        request_body = {'user_name': 'abcd'}
        with self.assertRaises(Exception) as context:
            SlackHelper.require_user(request_body, 'user')
        self.assertTrue('Command required to be run by user' in context.exception)

    def test_require_user(self):
        request_body = {'user_name': 'user'}
        SlackHelper.require_user(request_body, 'user')

    def test_require_channel_false(self):
        request_body = {'channel_name': 'abcd'}
        with self.assertRaises(Exception) as context:
            SlackHelper.require_channel(request_body, 'test')
        self.assertTrue('Command required to be run in #test' in context.exception)

    def test_require_channel(self):
        request_body = {'channel_name': 'test'}
        SlackHelper.require_channel(request_body, 'test')
