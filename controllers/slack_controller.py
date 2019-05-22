import json
import logging
import webapp2

from helpers.modqueue_helper import ModQueueHelper
from helpers.slack_helper import SlackHelper

from sitevars.slack_commands import SlackCommands


# Steps for adding a new Slack command are the following
# 1) Create a new Slash command in the Slack Directory
#   https://the-blue-alliance.slack.com/apps/A0F82E8CA-slash-commands
# 2) Write some command handler here and wire it up in `slack_main.py`
# 3) In your command handler, be sure to call `self._verify_command` for your command name
# 4) Add the command + token via the Admin page in TBA
#   http://www.thebluealliance.com/admin/slack_commands
# 5) Be sure to point your Slash command URL to the newly added URL in `slack_main.py`


class ModQueue(webapp2.RequestHandler):
    """
    /modqueue - Refresh the mod queue message
    """
    def post(self):
        json_dict = json.loads(self.request.body)
        SlackHelper.verify_command(json_dict, '/modqueue')
        SlackHelper.require_channel(json_dict, 'mods')
        ModQueueHelper.nag_mods()
