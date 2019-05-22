import json

from models.sitevar import Sitevar


class SlackCommands(object):
    # Key is the Slack command, value is the token to verify against

    @staticmethod
    def commands():
        slack_command_tokens_sitevar = Sitevar.get_or_insert('slack_commands', values_json=json.dumps({}))
        return slack_command_tokens_sitevar.contents

    @staticmethod
    def token(command):
        slack_command_tokens_sitevar = Sitevar.get_or_insert('slack_commands', values_json=json.dumps({}))
        return slack_command_tokens_sitevar.contents.get(command, None)

    @staticmethod
    def delete_command(command):
        slack_command_tokens_sitevar = Sitevar.get_or_insert('slack_commands', values_json=json.dumps({}))
        slack_command_tokens = slack_command_tokens_sitevar.contents
        slack_command_tokens.pop(command, None)
        slack_command_tokens_sitevar.contents = slack_command_tokens
        slack_command_tokens_sitevar.put()

    @staticmethod
    def set_token(command, token):
        slack_command_tokens_sitevar = Sitevar.get_or_insert('slack_commands', values_json=json.dumps({}))
        slack_command_tokens = slack_command_tokens_sitevar.contents
        slack_command_tokens[command] = token
        slack_command_tokens_sitevar.contents = slack_command_tokens
        slack_command_tokens_sitevar.put()
