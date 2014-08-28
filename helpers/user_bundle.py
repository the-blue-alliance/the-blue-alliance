import webapp2
from webapp2_extras import auth, sessions
from google.appengine.api import users

from models.account import Account


class UserBundle(object):
    """
    UserBundle encapsulates a bunch of Google AppEngine user management stuff
    to make it easier for templates.
    """
    def __init__(self):
        self._account = None

    @property
    def account(self):
        if self._account is None:
            self._account = Account.get_or_insert(
                self.current_user.get_id(),
                email = self.current_user.email,
                nickname = self.current_user.name,
                display_name = self.current_user.name)
        return self._account

    @webapp2.cached_property
    def auth(self):
        return auth.get_auth()

    @webapp2.cached_property
    def current_user(self):
      """Returns currently logged in user"""
      user_dict = self.auth.get_user_by_session()
      return self.auth.store.user_model.get_by_id(user_dict['user_id'])

    @property
    def user(self):
        return users.get_current_user()

    @property
    def is_current_user_admin(self):
        return users.is_current_user_admin()

    @property
    def login_url(self):
        return users.create_login_url("/")

    @property
    def logout_url(self):
        return users.create_logout_url("/")

    def create_login_url(self, target_url="/"):
        return users.create_login_url(target_url)
