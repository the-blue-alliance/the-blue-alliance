from sitevars.slack_commands import SlackCommands


class SlackHelper:

    @staticmethod
    def require_channel(json_dict, channel_name):
        if channel_name != json_dict.get('channel_name'):
            raise Exception('Command required to be run in #{}'.format(channel_name))


    @staticmethod
    def require_user(json_dict, user_name):
        if user_name != json_dict.get('user_name'):
            raise Exception('Command required to be run by {}'.format(user_name))


    @staticmethod
    def verify_command(json_dict, command):
        if command != json_dict.get('command'):
            raise Exception('Command required to be {}'.format(command))

        command_token = SlackCommands.token(command)
        if not command_token:
            raise Exception('No token for command {}'.format(command))

        token = json_dict.get('token')
        if not token:
            raise Exception('No token from request for command {}'.format(command))

        if command_token != token:
            raise Exception('Tokens do not match for command: {}'.format(command))
