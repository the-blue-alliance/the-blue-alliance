import os
import logging
from google.appengine.ext import ndb
from google.appengine.ext import deferred
from google.appengine.ext.webapp import template
from controllers.base_controller import LoggedInHandler

from models.event import Event
from models.event_details import EventDetails
from helpers.event_details_manipulator import EventDetailsManipulator
from helpers.match_helper import MatchHelper
from helpers.rankings_helper import RankingsHelper


def create_event_details(event_key):
  event = Event.get_by_id(event_key)
  if event.alliance_selections or event.district_points or event.matchstats or event.rankings:
    event_details = EventDetails(
      id=event_key,
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


class AdminMigrationRankings(LoggedInHandler):
  def get(self, year):
    self._require_admin()

    event_keys = Event.query(Event.year==int(year)).fetch(keys_only=True)
    event_details = ndb.get_multi([ndb.Key(EventDetails, key.id()) for key in event_keys])
    updated = []
    for event_detail in event_details:
      if event_detail:
        logging.info(event_detail.key.id())
        event_detail.rankings2 = RankingsHelper.convert_rankings(event_detail)
        updated.append(event_detail)
    EventDetailsManipulator.createOrUpdate(updated)

    self.response.out.write("DONE")


class AdminMigrationAddSurrogates(LoggedInHandler):
  def get(self, year):
    self._require_admin()

    events = Event.query(Event.year==int(year)).fetch()
    for event in events:
      deferred.defer(MatchHelper.add_surrogates, event, _queue="admin")

    self.response.out.write("DONE")
