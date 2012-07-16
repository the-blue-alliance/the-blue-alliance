import os

from google.appengine.api.users import User
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template, util


class AdminMain(webapp.RequestHandler):
    def get(self):
        
        user = User()
        
        template_values = {
            "user": user,
        }
        
        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/index.html')
        self.response.out.write(template.render(path, template_values))

class AdminDebugHandler(webapp.RequestHandler):
    def get(self):
        path = os.path.join(os.path.dirname(__file__), '../../templates/debug.html')
        self.response.out.write(template.render(path, {}))