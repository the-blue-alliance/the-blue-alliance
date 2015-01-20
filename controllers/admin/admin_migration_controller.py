import os
from google.appengine.ext.webapp import template
from controllers.base_controller import LoggedInHandler


class AdminMigration(LoggedInHandler):
  def get(self):
    self._require_admin()
    path = os.path.join(os.path.dirname(__file__), '../../templates/admin/migration.html')
    self.response.out.write(template.render(path, self.template_values))
