import Cookie
import os

from google.appengine.api import users
from google.appengine.ext import ndb, webapp
from google.appengine.ext.webapp import template

import tba_config

from base_controller import LoggedInHandler
from helpers.user_bundle import UserBundle

from models.account import Account

class AccountOverview(LoggedInHandler):
    def get(self):
        self._require_login('/account')
        # Redirects to registration page if account not registered
        if not self.user_bundle.account.registered:
            self.redirect('/account/register')
            return None
        path = os.path.join(os.path.dirname(__file__), '../templates/account/overview.html')
        self.response.out.write(template.render(path, self.template_values))

class AccountEdit(LoggedInHandler):
    def get(self):
        self._require_login('/account/edit')
        if not self.user_bundle.account.registered:
            self.redirect('/account/register')
            return None

        path = os.path.join(os.path.dirname(__file__), '../templates/account/edit.html')
        self.response.out.write(template.render(path, self.template_values))

    def post(self):
        self._require_login('/account/edit')
        if not self.user_bundle.account.registered:
            self.redirect('/account/register')
            return None

        # Check to make sure that they aren't trying to edit another user
        real_account_id = self.user_bundle.account.key.id()
        check_account_id = self.request.get('account_id')
        if check_account_id == real_account_id:
            user = Account.get_by_id(self.user_bundle.account.key.id())
            user.name = self.request.get('name')
            user.put()
            self.redirect('/account')
        else:
            self.redirect('/')

class AccountRegister(LoggedInHandler):
    def get(self):
        self._require_login('/account/register')
        # Redirects to account overview page if already registered
        if self.user_bundle.account.registered:
            self.redirect('/account')
            return None

        path = os.path.join(os.path.dirname(__file__), '../templates/account/register.html')
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
            user = Account.get_by_id(self.user_bundle.account.key.id())
            user.name = self.request.get('name')
            user.registered = True
            user.put()
            self.redirect('/account')
        else:
            self.redirect('/')

class AccountLogout(LoggedInHandler):
  def get(self):
    if os.environ.get('SERVER_SOFTWARE', '').startswith('Development/'):
      self.redirect(self.user_bundle.logout_url)
      return

    # Deletes the session cookies pertinent to TBA without touching Google session(s)
    response = self.redirect('/') 
    response.delete_cookie('ACSID')
    response.delete_cookie('SACSID')

    return response
