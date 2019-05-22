import unittest2
import webapp2
import webtest

from controllers.slack_controller import ModQueue

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from sitevars.slack_commands import SlackCommands


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
            ('/modqueue', ModQueue),
        ])
        self.testapp = webtest.TestApp(app)

    def tearDown(self):
        self.testbed.deactivate()

    def test_modqueue_command(self):
        with self.assertRaises(Exception) as e:
            response = self.testapp.post_json('/modqueue', {'channel_name': 'mods', 'token': 'defg'})
            self.assertTrue('Command required to be /modqueue' in e)
            self.assertEqual(response.status_code, 500)

    def test_modqueue_token(self):
        with self.assertRaises(Exception) as e:
            response = self.testapp.post_json('/modqueue', {'channel_name': 'mods', 'token': 'defg', 'command': '/modqueue'})
            self.assertTrue('Tokens do not match for command: /modqueue' in e)
            self.assertEqual(response.status_code, 500)

    def test_modqueue_channel(self):
        with self.assertRaises(Exception) as e:
            response = self.testapp.post_json('/modqueue', {'channel_name': 'notmods', 'token': 'abcd', 'command': '/modqueue'})
            self.assertTrue('Tokens do not match for command: /modqueue' in e)
            self.assertEqual(response.status_code, 500)

    def test_modqueue(self):
        response = self.testapp.post_json('/modqueue', {'command': '/modqueue', 'token': 'abcd', 'channel_name': 'mods'})
        self.assertEqual(response.status_code, 200)
