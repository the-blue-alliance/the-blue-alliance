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
                self.user.user_id(),
                email = self.user.email(),
                nickname = self.user.nickname())
        return self._account

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
