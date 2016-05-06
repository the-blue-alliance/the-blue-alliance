import os
import logging
from google.appengine.ext import ndb
from google.appengine.ext import deferred
from google.appengine.ext.webapp import template
from controllers.base_controller import LoggedInHandler

from models.event import Event
from models.event_details import EventDetails
from helpers.event_details_manipulator import EventDetailsManipulator


def create_event_details(event_key):
  event = Event.get_by_id(event_key)
  event_details = EventDetails(
    id=event_key,
    parent=event.key,
    alliance_selections=event.alliance_selections,
    district_points=event.district_points,
    matchstats=event.matchstats,
    rankings=event.rankings)
  EventDetailsManipulator.createOrUpdate(event_details)


class AdminMigration(LoggedInHandler):
  def get(self):
    self._require_admin()
    path = os.path.join(os.path.dirname(__file__), '../../templates/admin/migration.html')
    self.response.out.write(template.render(path, self.template_values))


class AdminMigrationCreateEventDetails(LoggedInHandler):
  def get(self):
    self._require_admin()
    for event_key in Event.query().fetch(keys_only=True):
      deferred.defer(create_event_details, event_key.id(), _queue="admin")

    self.response.out.write("DONE")
