import json
import logging
import webapp2

from helpers.modqueue_helper import ModQueueHelper

from sitevars.slack_commands import SlackCommands


# Steps for adding a new Slack command are the following
# 1) Create a new Slash command in the Slack Directory
#   https://the-blue-alliance.slack.com/apps/A0F82E8CA-slash-commands
# 2) Write some command handler here and wire it up in `slack_main.py`
# 3) In your command handler, be sure to call `self._verify_command` for your command name
# 4) Add the command + token via the Admin page in TBA
#   http://www.thebluealliance.com/admin/slack_commands
# 5) Be sure to point your Slash command URL to the newly added URL in `slack_main.py`


class SlackHandler(webapp2.RequestHandler):

    def require_channel(self, channel_name):
        if channel_name != self.request.get('channel_name'):
            raise Exception('Command required to be run in #{}'.format(channel_name))

    def require_user(self, user_name):
        if user_name != self.request.get('user_name'):
            raise Exception('Command required to be run by {}'.format(user_name))

    def verify_command(self, command):
        if command != self.request.get('command'):
            raise Exception('Command required to be {}'.format(command))

        command_token = SlackCommands.token(command)
        if not command_token:
            raise Exception('No token for command {}'.format(command))

        token = self.request.get('token')
        if not token:
            raise Exception('No token from request for command {}'.format(command))

        if command_token != token:
            raise Exception('Tokens do not match for command: {}'.format(command))


class ModQueueHandler(SlackHandler):
    """
    /modqueue - Refresh the mod queue message
    """
    def get(self):
        self.verify_command('/modqueue')
        self.require_channel('mods')
        ModQueueHelper.nag_mods()
