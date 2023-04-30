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


class AdminUserPermissionsList(LoggedInHandler):
    """
    List all Users with Permissions.
    """
    def get(self):
        self._require_admin()
        users = Account.query(Account.permissions != None).fetch()

        self.template_values.update({
            "users": users,
            "permissions": AccountPermissions.permissions,
        })

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/user_permissions_list.html')
        self.response.out.write(template.render(path, self.template_values))


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

