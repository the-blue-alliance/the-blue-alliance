import os

from google.appengine.ext.webapp import template

from controllers.base_controller import LoggedInHandler

class AdminMain(LoggedInHandler):
    def get(self):
        self._require_admin()
        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/index.html')
        self.response.out.write(template.render(path, self.template_values))

class AdminDebugHandler(LoggedInHandler):
    def get(self):
        self._require_admin()
        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/debug.html')
        self.response.out.write(template.render(path, self.template_values))

class AdminTasksHandler(LoggedInHandler):
    def get(self):
        self._require_admin()
        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/tasks.html')
        self.response.out.write(template.render(path, self.template_values))