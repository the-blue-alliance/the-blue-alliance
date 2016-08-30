from datetime import datetime
import logging
import os

from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.ext.webapp import template

from controllers.base_controller import LoggedInHandler
from consts.account_permissions import AccountPermissions
from models.account import Account

import tba_config

class AdminUserList(LoggedInHandler):
    """
    List all Users.
    """
    def get(self):
        self._require_admin()
        users = Account.query().order(Account.created).fetch()

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
            "user": user,
            "permissions": AccountPermissions.permissions
        })

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/user_details.html')
        self.response.out.write(template.render(path, self.template_values))


class AdminUserEdit(LoggedInHandler):
    """
    Edit a User.
    """
    def get(self, user_id):
        self._require_admin()
        user = Account.get_by_id(user_id)
        self.template_values.update({
            "user": user,
            "permissions": AccountPermissions.permissions
        })

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/user_edit.html')
        self.response.out.write(template.render(path, self.template_values))

    def post(self, user_id):
        self._require_admin()
        user = Account.get_by_id(user_id)

        user.display_name = self.request.get("display_name")
        user.permissions = []
        for enum in AccountPermissions.permissions:
            permcheck = self.request.get("perm-" + str(enum))
            if permcheck :
                user.permissions.append(enum)
        user.put()

        self.redirect("/admin/user/" + user_id)


class AdminUserTestSetup(LoggedInHandler):
    """
    Gives the current user all permissions. For testing only.
    """
    def get(self):
        self._require_admin()

        if tba_config.CONFIG["env"] != "prod":
            account = Account.get_by_id(self.user_bundle.account.key.id())
            account.display_name = "Test User"
            account.registered = True
            account.permissions = AccountPermissions.permissions.keys()
            account.put()

            self.redirect("/admin/user/" + account.key.id())
        else:
            logging.error("{} tried to set up a test user in prod! No can do.".format(
                self.user_bundle.user.email()))
            self.redirect("/admin/")

