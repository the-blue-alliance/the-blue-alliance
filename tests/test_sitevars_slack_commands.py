import json
import unittest2

from google.appengine.ext import testbed

from models.sitevar import Sitevar
from sitevars.slack_commands import SlackCommands


class TestSlackCommands(unittest2.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        Sitevar(id='slack_commands', values_json=json.dumps({'/modqueue': 'abcd'})).put()
        self.slack_commands = SlackCommands()

    def tearDown(self):
        self.testbed.deactivate()

    def test_commands(self):
        self.assertEqual(self.slack_commands.commands(), {'/modqueue': 'abcd'})

    def test_token(self):
        self.assertEqual(self.slack_commands.token('/modqueue'), 'abcd')
        self.assertIsNone(self.slack_commands.token('/nocommand'))

    def test_delete_command(self):
        self.assertEqual(self.slack_commands.token('/modqueue'), 'abcd')
        self.slack_commands.delete_command('/modqueue')
        self.assertIsNone(self.slack_commands.token('/modqueue'))
        self.slack_commands.delete_command('/nocommand')

    def test_set_token(self):
        self.assertEqual(self.slack_commands.token('/modqueue'), 'abcd')
        self.slack_commands.set_token('/modqueue', 'hijkl')
        self.assertEqual(self.slack_commands.token('/modqueue'), 'hijkl')

        self.assertIsNone(self.slack_commands.token('/nocommand'))
        self.slack_commands.set_token('/nocommand', 'abcd')
        self.assertEqual(self.slack_commands.token('/nocommand'), 'abcd')
