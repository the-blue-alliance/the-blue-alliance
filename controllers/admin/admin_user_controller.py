from datetime import datetime
import logging
import os

from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.ext.webapp import template

from controllers.base_controller import LoggedInHandler
from models.account import Account

class AdminUserList(LoggedInHandler):
    """
    List all Users.
    """
    def get(self):
        self._require_admin()
        users = Account.query().fetch(10000)
        
        self.template_values.update({
            "users": users,
        })
        
        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/user_list.html')
        self.response.out.write(template.render(path, self.template_values))

class AdminUserDetail(LoggedInHandler):
    """
    Show a User.
    """
    def get(self, user_id):
        self._require_admin()
        user = Account.get_by_id(user_id)

        self.template_values.update({
            "user": user
        })

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/user_details.html')
        self.response.out.write(template.render(path, self.template_values))

class AdminUserDelete(LoggedInHandler):
    """
    Delete a User.
    """
    def get(self, user_id):
        self._require_admin()
        user = Account.get_by_id(user_id)

        self.template_values.update({
            "user": user
        })

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/user_delete.html')
        self.response.out.write(template.render(path, self.template_values))

    def post(self, user_id):
        self._require_admin()
        user = Account.get_by_id(user_id)
        logging.warning("Deleting %s at the request of %s" % (
            user.nickname,
            users.get_current_user().nickname()))
        ndb.Key(Account, user_id).delete()

        self.redirect("/admin/users?deleted=%s" % user_id)


class AdminUserEdit(LoggedInHandler):
    """
    Edit a User.
    """
    def get(self, user_id):
        self._require_admin()
        user = Account.get_by_id(user_id)
        self.template_values.update({
            "user": user
        })

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/user_edit.html')
        self.response.out.write(template.render(path, self.template_values))

    def post(self, user_id):
        self._require_admin()
        user = Account.get_by_id(user_id)

        user.name = self.request.get("name")
        user.email = self.request.get("email")
        user.put()

        self.redirect("/admin/user/" + user_id)
