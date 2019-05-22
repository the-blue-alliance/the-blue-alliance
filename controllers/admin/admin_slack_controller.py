import os

from google.appengine.ext.webapp import template

from controllers.base_controller import LoggedInHandler

from sitevars.slack_commands import SlackCommands


class AdminSlackCommandsList(LoggedInHandler):
    """
    Manage Slack slash commands.
    """

    def get(self):
        self._require_admin()

        slack_commands = SlackCommands.commands()
        # Remove leading / because Jinja 1 is terrible
        slack_commands = {key[1:]: slack_commands[key] for key in slack_commands.keys()}
        self.template_values.update({
            "commands": slack_commands,
        })

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/slack_commands.html')
        self.response.out.write(template.render(path, self.template_values))

    def post(self):
        self._require_admin()

        command_name = self.request.get('command', None)
        if not command_name:
            self.redirect('/admin/slack_commands')
            return

        # Make sure we can either enter a `/command` or just a `command` name
        # and that we always store the command with a leading slash
        if command_name[0] == '/':
            command = command_name
        else:
            command = '/{}'.format(command_name)

        # If the command exists and we're looking to update the token, make sure the tokens match
        # Otherwise, we'll assume the command is new and insert it.
        current_token = SlackCommands.token(command)
        if current_token:
            previous_token = self.request.get('previous_token', None)
            if current_token != previous_token:
                self.redirect('/admin/slack_commands')
                return

        # Verify our new token is non-None
        token = self.request.get('token', None)
        if not token:
            self.redirect('/admin/slack_commands')
            return

        SlackCommands.set_token(command, token)

        self.redirect('/admin/slack_commands')


class AdminSlackCommandsDelete(LoggedInHandler):
    """
    Manage Slack slash commands.
    """

    def post(self, command_name):
        self._require_admin()

        if not command_name:
            self.redirect('/admin/slack_commands')
            return

        command = '/{}'.format(command_name)

        # Make sure we've passed the proper token to delete this command
        # This prevents some garbage post from deleting tokens.
        current_token = SlackCommands.token(command)
        if not current_token:
            self.redirect('/admin/slack_commands')
            return

        token = self.request.get('token', None)
        if not token:
            self.redirect('/admin/slack_commands')
            return

        if current_token != token:
            self.redirect('/admin/slack_commands')
            return

        SlackCommands.delete_command(command)

        self.redirect('/admin/slack_commands')
