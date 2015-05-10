import os
import logging
from google.appengine.ext import ndb
from google.appengine.ext import deferred
from google.appengine.ext.webapp import template
from controllers.base_controller import LoggedInHandler

from models.event import Event
from helpers.match_manipulator import MatchManipulator


def add_events_from_year(year):
  event_keys = Event.query(Event.year == year).fetch(keys_only=True)
  for event_key in event_keys:
    deferred.defer(add_year, event_key, _queue="admin")


def add_year(event_key):
  logging.info(event_key)
  matches = event_key.get().matches
  if matches:
    for match in matches:
      match.year = int(match.event.id()[:4])
      match.dirty = True
      MatchManipulator.createOrUpdate(match)


class AdminMigration(LoggedInHandler):
  def get(self):
    self._require_admin()
    path = os.path.join(os.path.dirname(__file__), '../../templates/admin/migration.html')
    self.response.out.write(template.render(path, self.template_values))


class AdminMigrationAddMatchYear(LoggedInHandler):
  def get(self):
    self._require_admin()
    for year in range(1992, 2016):
      deferred.defer(add_events_from_year, year, _queue="admin")

    self.response.out.write("DONE")
