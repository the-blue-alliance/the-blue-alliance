import logging
from datetime import datetime
import os

from google.appengine.api import users
from google.appengine.ext import webapp, db
from google.appengine.ext import ndb
from google.appengine.ext.webapp import template
from webapp2_extras import auth
from webapp2_extras.appengine.auth.models import User
from webapp2_extras.appengine.auth.models import Unique

class AdminUserList(webapp.RequestHandler):
    """
    List all Users.
    """
    def get(self):
        users = User.query().fetch(10000)
        
        template_values = {
            "users": users,
        }
        
        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/user_list.html')
        self.response.out.write(template.render(path, template_values))

class AdminUserDetail(webapp.RequestHandler):
    """
    Show a User.
    """
    def get(self, user_id):
        user = auth.get_auth().store.user_model.get_by_id(int(user_id))

        template_values = {
            "user": user
        }

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/user_details.html')
        self.response.out.write(template.render(path, template_values))

class AdminUserDelete(webapp.RequestHandler):
    """
    Delete a User.
    """
    def get(self, user_id):
        user = auth.get_auth().store.user_model.get_by_id(int(user_id))

        template_values = {
            "user": user
        }

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/user_delete.html')
        self.response.out.write(template.render(path, template_values))

    def post(self, user_id):
        user = auth.get_auth().store.user_model.get_by_id(int(user_id))
        logging.warning("Deleting %s at the request of %s / %s" % (
            user,
            users.get_current_user().user_id(),
            users.get_current_user().email()))
        ndb.Key(User, int(user_id)).delete()
        UNIQUE_AUTH_ID_KEYS = []
        for auth_id in user.auth_ids:
            UNIQUE_AUTH_ID_KEYS.append('User.auth_id:'+auth_id)
        Unique.delete_multi(UNIQUE_AUTH_ID_KEYS)

        self.redirect("/admin/users?deleted=%s" % user_id)


class AdminUserEdit(webapp.RequestHandler):
    """
    Edit a User.
    """
    def get(self, user_id):
        user = auth.get_auth().store.user_model.get_by_id(int(user_id))
        template_values = {
            "user": user
        }

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/user_edit.html')
        self.response.out.write(template.render(path, template_values))

    def post(self, user_id):
        user = auth.get_auth().store.user_model.get_by_id(int(user_id))

        user.name = self.request.get("name")
        user.email = self.request.get("email")
        user.put()

        self.redirect("/admin/user/" + user_id)
