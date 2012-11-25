import os

from helpers.admin_helper import AdminHelper

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

class AdminMain(webapp.RequestHandler):
    def get(self):
        
        user = AdminHelper.getCurrentUser()
        
        template_values = {
            "user": user,
        }
        
        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/index.html')
        self.response.out.write(template.render(path, template_values))

class AdminDebugHandler(webapp.RequestHandler):
    def get(self):
        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/debug.html')
        self.response.out.write(template.render(path, {}))

class AdminTasksHandler(webapp.RequestHandler):
    def get(self):
        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/tasks.html')
        self.response.out.write(template.render(path, {}))