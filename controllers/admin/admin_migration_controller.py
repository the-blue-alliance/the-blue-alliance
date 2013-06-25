import os
from google.appengine.ext import ndb
from google.appengine.ext.webapp import template
from controllers.base_controller import LoggedInHandler
from models.event import Event, EventType
from helpers.event_helper import EventHelper


class AdminMigration(LoggedInHandler):
  def get(self):
    self._require_admin()
    path = os.path.join(os.path.dirname(__file__), '../../templates/admin/migration.html')
    self.response.out.write(template.render(path, self.template_values))

class AdminMigrationUpdateEventType(LoggedInHandler):
  def get(self):
    self._require_admin()
    
    events = Event.query().order(Event.year).order(Event.start_date).fetch(10000)
    for event in events:
      event.new_event_type = EventType.type_names[EventHelper.parseEventType(event.event_type)]
    
    self.template_values.update({"events": events})
    path = os.path.join(os.path.dirname(__file__), '../../templates/admin/event_type_migration.html')
    self.response.out.write(template.render(path, self.template_values))

class AdminMigrationUpdateEventTypeAccept(LoggedInHandler):
  def post(self):
    self._require_admin()
    
    events = Event.query().order(Event.year).order(Event.start_date).fetch(10000)
    for event in events:
      event.type = EventType.type_names[EventHelper.parseEventType(event.event_type)]
    ndb.put_multi(events)
    
    self.redirect("/admin/events")
