import os

from google.appengine.ext.webapp import template

from controllers.base_controller import LoggedInHandler
from models.account import Account


class AdminUserList(LoggedInHandler):
    """
    List all Users.
    """
    def get(self):
        self._require_admin()
        users = Account.query().order(Account.created).fetch(10000)

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

        user.display_name = self.request.get("display_name")
        user.put()

        self.redirect("/admin/user/" + user_id)
