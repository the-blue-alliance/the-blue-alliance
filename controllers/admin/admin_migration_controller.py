import os
from google.appengine.ext import ndb
from google.appengine.ext.webapp import template
from consts.event_type import EventType
from controllers.base_controller import LoggedInHandler
from models.award import Award
from models.event import Event
from helpers.event_helper import EventHelper


class AdminMigration(LoggedInHandler):
  def get(self):
    self._require_admin()
    path = os.path.join(os.path.dirname(__file__), '../../templates/admin/migration.html')
    self.response.out.write(template.render(path, self.template_values))


class AdminMigrationDeleteAwards(LoggedInHandler):
  def get(self):
    self._require_admin()
    award_keys = Award.query().fetch(100000, keys_only=True)
    ndb.delete_multi(award_keys)
    self.response.out.write("Deleted {} awards!".format(len(award_keys)))
