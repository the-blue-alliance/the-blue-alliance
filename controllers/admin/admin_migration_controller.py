import os
from google.appengine.ext import ndb
from google.appengine.ext.webapp import template
from consts.event_type import EventType
from controllers.base_controller import LoggedInHandler
from models.event import Event
from helpers.event_helper import EventHelper
from models.account import Account


class AdminMigration(LoggedInHandler):
  def get(self):
    self._require_admin()
    path = os.path.join(os.path.dirname(__file__), '../../templates/admin/migration.html')
    self.response.out.write(template.render(path, self.template_values))


class AdminMigrationReindexAccount(LoggedInHandler):
  def get(self):
    self._require_admin()
    account_keys = Account.query().fetch(1000, keys_only=True)
    accounts = ndb.get_multi(account_keys)
    ndb.put_multi(accounts)
    self.response.out.write("DONE!")
