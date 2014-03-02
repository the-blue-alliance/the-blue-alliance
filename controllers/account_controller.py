import os
import json

from google.appengine.ext.webapp import template

from base_controller import LoggedInHandler

from models.account import Account


class AccountOverview(LoggedInHandler):
    def get(self):
        self._require_login('/account')
        # Redirects to registration page if account not registered
        if not self.user_bundle.account.registered:
            self.redirect('/account/register')
            return None
        path = os.path.join(os.path.dirname(__file__), '../templates/account_overview.html')
        self.response.out.write(template.render(path, self.template_values))


class AccountEdit(LoggedInHandler):
    def get(self):
        self._require_login('/account/edit')
        if not self.user_bundle.account.registered:
            self.redirect('/account/register')
            return None

        # Autofill template with user's team and event preferences
        self.template_values['teams_following'] = []
        self.template_values['events_following'] = []

        if self.user_bundle.account.follow_teams_json:
            self.template_values['teams_following'] = ",".join(json.loads(self.user_bundle.account.follow_teams_json))
        if self.user_bundle.account.follow_events_json:
            self.template_values['events_following'] = ",".join(json.loads(self.user_bundle.account.follow_events_json))
        if self.user_bundle.account.gameday_preferences:
            self.template_values['gameday_layout'] = json.loads(self.user_bundle.account.gameday_preferences)['layout']
            self.template_values['gameday_scheme'] = json.loads(self.user_bundle.account.gameday_preferences)['scheme']

        path = os.path.join(os.path.dirname(__file__), '../templates/account_edit.html')
        self.response.out.write(template.render(path, self.template_values))

    def post(self):
        self._require_login('/account/edit')
        if not self.user_bundle.account.registered:
            self.redirect('/account/register')
            return None

        # TODO: Move to manipulator
        user = Account.get_by_id(self.user_bundle.account.key.id())
        user.display_name = self.request.get('display_name')
        user.gameday_preferences = json.dumps({"layout":int(self.request.get('gameday_layout')), "scheme":self.request.get('gameday_scheme')})
        follow_teams = self.request.get('follow_teams').split(',')
        user.follow_teams_json = json.dumps(follow_teams)
        follow_events = self.request.get('follow_events').split(',')
        user.follow_events_json = json.dumps(follow_events)

        user.put()
        self.redirect('/account')

class AccountRegister(LoggedInHandler):
    def get(self):
        self._require_login('/account/register')
        # Redirects to account overview page if already registered
        if self.user_bundle.account.registered:
            self.redirect('/account')
            return None

        path = os.path.join(os.path.dirname(__file__), '../templates/account_register.html')
        self.response.out.write(template.render(path, self.template_values))

    def post(self):
        self._require_login('/account/register')
        if self.user_bundle.account.registered:
            self.redirect('/account')
            return None

        # Check to make sure that they aren't trying to edit another user
        real_account_id = self.user_bundle.account.key.id()
        check_account_id = self.request.get('account_id')
        if check_account_id == real_account_id:
            account = Account.get_by_id(self.user_bundle.account.key.id())
            account.display_name = self.request.get('display_name')
            account.registered = True
            account.put()
            self.redirect('/account')
        else:
            self.redirect('/')


class AccountLogout(LoggedInHandler):
    def get(self):
        if os.environ.get('SERVER_SOFTWARE', '').startswith('Development/'):
            self.redirect(self.user_bundle.logout_url)
            return

        # Deletes the session cookies pertinent to TBA without touching Google session(s)
        # Reference: http://ptspts.blogspot.ca/2011/12/how-to-log-out-from-appengine-app-only.html
        response = self.redirect('/')
        response.delete_cookie('ACSID')
        response.delete_cookie('SACSID')

        return response
