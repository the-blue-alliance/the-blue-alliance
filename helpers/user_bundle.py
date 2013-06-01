from google.appengine.api import users

class UserBundle(object):
    """
    UserBundle encapsulates a bunch of Google AppEngine user management stuff
    to make it easier for templates.
    """
    @property
    def user(self):
        return users.get_current_user()

    @property
    def is_current_user_admin(self):
        return users.is_current_user_admin()

    @property
    def login_url(self):
        return users.create_login_url("/dashboard")

    @property
    def logout_url(self):
        return users.create_login_url("/")
