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
    PAGE_SIZE = 1000

    def get(self, page_num=0):
        self._require_admin()
        page_num = int(page_num)

        num_users = Account.query().count()
        max_page = num_users / self.PAGE_SIZE

        if page_num <= max_page:
            offset=self.PAGE_SIZE*page_num
        else:
            page_num = 0
            offset = 0
        users = Account.query().order(Account.created).fetch(self.PAGE_SIZE, offset=offset)

        self.template_values.update({
            "num_users": num_users,
            "users": users,
            "page_num": page_num,
            "page_labels": [p+1 for p in xrange(max_page+1)],
        })

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/user_list.html')
        self.response.out.write(template.render(path, self.template_values))


class AdminUserLookup(LoggedInHandler):
    """
    Lookup a single user by email
    """
    def get(self):
        self._require_admin()
        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/user_lookup.html')
        self.response.out.write(template.render(path, self.template_values))

    def post(self):
        self._require_admin()
        user_email = self.request.get('email')
        if not user_email:
            self.abort(404)
        users = Account.query(Account.email == user_email).fetch()
        if not users:
            self.abort(404)
        user = users[0]
        self.redirect('/admin/user/edit/{}'.format(user.key.id()))


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
        user.shadow_banned = True if self.request.get("shadow_banned") else False
        user.permissions = []
        for enum in AccountPermissions.permissions:
            permcheck = self.request.get("perm-" + str(enum))
            if permcheck:
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

