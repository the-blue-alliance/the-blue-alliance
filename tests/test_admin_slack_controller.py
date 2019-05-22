import unittest2
import webapp2
import webtest

from controllers.admin.admin_slack_controller import AdminSlackCommandsList, AdminSlackCommandsDelete

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from models.account import Account

from sitevars.slack_commands import SlackCommands


class TestAdminSlackController(unittest2.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_user_stub()
        self.testbed.init_urlfetch_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        app = webapp2.WSGIApplication([
            ('/admin/slack_commands', AdminSlackCommandsList),
            ('/admin/slack_commands/delete/(.*)', AdminSlackCommandsDelete),
        ])
        self.testapp = webtest.TestApp(app)

    def tearDown(self):
        self.testbed.deactivate()

    def loginUser(self):
        self.testbed.setup_env(
            user_email="user@example.com",
            user_id="123",
            user_is_admin='1',
            overwrite=True)

        self.account = Account.get_or_insert("123", email="user@example.com", registered=True)

    def test_login_redirect_list(self):
        response = self.testapp.get('/admin/slack_commands', status='3*')
        response = response.follow(expect_errors=True)
        self.assertTrue(response.request.path.startswith("/account/login_required"))

    def test_login_redirect_list_post(self):
        response = self.testapp.post('/admin/slack_commands', status='3*')
        response = response.follow(expect_errors=True)
        self.assertTrue(response.request.path.startswith("/account/login_required"))

    def test_login_redirect_delete(self):
        response = self.testapp.post('/admin/slack_commands/delete/something', status='3*')
        response = response.follow(expect_errors=True)
        self.assertTrue(response.request.path.startswith("/account/login_required"))

    def test_list(self):
        self.loginUser()
        response = self.testapp.get('/admin/slack_commands')
        self.assertEqual(response.status_int, 200)

        # Shows our add button
        add_command_form = response.forms.get('add-command', None)
        self.assertIsNotNone(add_command_form)

    def test_list_show(self):
        SlackCommands.set_token('/modqueue', 'abcdefg')

        self.loginUser()
        response = self.testapp.get('/admin/slack_commands')
        self.assertEqual(response.status_int, 200)

        # Check that our commands are rendered
        response.mustcontain('/modqueue')
        response.mustcontain('abcdefg')

        update_command_form = response.forms.get('update-modqueue', None)
        self.assertIsNotNone(update_command_form)

        delete_command_form = response.forms.get('delete-modqueue', None)
        self.assertIsNotNone(delete_command_form)

        # Shows our add button
        add_command_form = response.forms.get('add-command', None)
        self.assertIsNotNone(add_command_form)

    def test_list_post_no_command(self):
        SlackCommands.set_token('/modqueue', 'abcdefg')

        self.loginUser()

        request_body = {}
        response = self.testapp.post('/admin/slack_commands', request_body)
        self.assertEqual(response.status_int, 302)
        self.assertTrue(response.request.path.startswith("/admin/slack_commands"))

        self.assertEqual(SlackCommands.token('/modqueue'), 'abcdefg')

    def test_list_post_no_token(self):
        self.loginUser()

        request_body = {'command': '/modqueue'}
        response = self.testapp.post('/admin/slack_commands', request_body)
        self.assertEqual(response.status_int, 302)
        self.assertTrue(response.request.path.startswith("/admin/slack_commands"))

    def test_list_post_wrong_token(self):
        SlackCommands.set_token('/modqueue', 'abcdefg')

        self.loginUser()

        request_body = {'command': '/modqueue', 'previous_token': 'abcdef'}
        response = self.testapp.post('/admin/slack_commands', request_body)
        self.assertEqual(response.status_int, 302)
        self.assertTrue(response.request.path.startswith("/admin/slack_commands"))

        self.assertEqual(SlackCommands.token('/modqueue'), 'abcdefg')

    def test_list_post_change_token(self):
        SlackCommands.set_token('/modqueue', 'abcdefg')

        self.loginUser()

        request_body = {'command': '/modqueue', 'previous_token': 'abcdefg', 'token': 'new'}
        response = self.testapp.post('/admin/slack_commands', request_body)
        self.assertEqual(response.status_int, 302)
        self.assertTrue(response.request.path.startswith("/admin/slack_commands"))

        self.assertEqual(SlackCommands.token('/modqueue'), 'new')

    def test_list_post_change_token_no_slash(self):
        SlackCommands.set_token('/modqueue', 'abcdefg')

        self.loginUser()

        request_body = {'command': 'modqueue', 'previous_token': 'abcdefg', 'token': 'new'}
        response = self.testapp.post('/admin/slack_commands', request_body)
        self.assertEqual(response.status_int, 302)
        self.assertTrue(response.request.path.startswith("/admin/slack_commands"))

        self.assertEqual(SlackCommands.token('/modqueue'), 'new')

    def test_list_delete_no_command(self):
        SlackCommands.set_token('/modqueue', 'abcdefg')

        self.loginUser()

        request_body = {}
        response = self.testapp.post('/admin/slack_commands/delete/', request_body)
        self.assertEqual(response.status_int, 302)
        self.assertTrue(response.request.path.startswith("/admin/slack_commands"))

        self.assertEqual(SlackCommands.token('/modqueue'), 'abcdefg')

    def test_list_delete_no_current_token(self):
        self.loginUser()

        request_body = {'token': 'abcd'}
        response = self.testapp.post('/admin/slack_commands/delete/modqueue', request_body)
        self.assertEqual(response.status_int, 302)
        self.assertTrue(response.request.path.startswith("/admin/slack_commands"))

        self.assertIsNone(SlackCommands.token('/modqueue'))

    def test_list_delete_wrong_token(self):
        SlackCommands.set_token('/modqueue', 'abcdefg')

        self.loginUser()

        request_body = {'token': 'abcd'}
        response = self.testapp.post('/admin/slack_commands/delete/modqueue', request_body)
        self.assertEqual(response.status_int, 302)
        self.assertTrue(response.request.path.startswith("/admin/slack_commands"))

        self.assertEqual(SlackCommands.token('/modqueue'), 'abcdefg')

    def test_list_delete(self):
        SlackCommands.set_token('/modqueue', 'abcdefg')

        self.loginUser()

        request_body = {'token': 'abcdefg'}
        response = self.testapp.post('/admin/slack_commands/delete/modqueue', request_body)
        self.assertEqual(response.status_int, 302)
        self.assertTrue(response.request.path.startswith("/admin/slack_commands"))

        self.assertIsNone(SlackCommands.token('/modqueue'))
